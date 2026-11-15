"""Reproduce local P0 component timings; never a deployed/browser SLA assertion."""

import argparse
import hashlib
import json
import math
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import app as app_module  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

NOW = datetime(2026, 11, 3, 12, 0, 0)
FIXTURE_CREDENTIALS = {"email": "timing@example.test", "password": "PublicDemo123!"}


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz is None else NOW.replace(tzinfo=tz)


def seed(database):
    with sqlite3.connect(database) as connection:
        connection.executescript((ROOT / "src/schema.sql").read_text())
        users = [(1, FIXTURE_CREDENTIALS["email"], "Timing Student", "student"),
                 (2, "lecturer@example.test", "Timing Lecturer", "lecturer")]
        users += [(n, f"feedback{n}@example.test", f"Student {n}", "student")
                  for n in range(3, 23)]
        hashed = generate_password_hash(FIXTURE_CREDENTIALS["password"])
        connection.executemany(
            "INSERT INTO users (id,email,password_hash,full_name,role,created_at) "
            "VALUES (?,?,?,?,?,?)",
            [(n, email, hashed, name, role, NOW.isoformat()) for n, email, name, role in users],
        )
        connection.execute(
            "INSERT INTO courses (id,course_code,course_name,created_at) "
            "VALUES (1,'TIMING101','Timing Course',?)", (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO course_lecturers (lecturer_id,course_id,assigned_at) VALUES (2,1,?)",
            (NOW.isoformat(),),
        )
        connection.executemany(
            "INSERT INTO course_enrollments (student_id,course_id,enrolled_at) VALUES (?,1,?)",
            [(n, NOW.isoformat()) for n in [1, *range(3, 23)]],
        )
        connection.executemany(
            "INSERT INTO evaluations (id,course_id,created_by,title,deadline,status,created_at) "
            "VALUES (?,1,2,?,?,'open',?)",
            [(n, f"Evaluation {n}", (NOW + timedelta(days=n + 1)).isoformat(),
              NOW.isoformat()) for n in (1, 2, 3)],
        )
        connection.executemany(
            "INSERT INTO questions "
            "(id,evaluation_id,question_text,question_type,is_required,question_order) "
            "VALUES (?,1,?,'rating',1,?)",
            [(n, f"Rating {n}", n) for n in range(1, 6)],
        )
        connection.execute(
            "INSERT INTO questions "
            "(id,evaluation_id,question_text,question_type,is_required,question_order) "
            "VALUES (6,1,'Comment','text',0,6)"
        )
        for student in range(3, 23):
            response = connection.execute(
                "INSERT INTO responses (evaluation_id,student_id,status,submitted_at) "
                "VALUES (1,?,'submitted',?)", (student, NOW.isoformat()),
            ).lastrowid
            connection.executemany(
                "INSERT INTO response_answers (response_id,question_id,rating_value) "
                "VALUES (?,?,3)", [(response, n) for n in range(1, 6)],
            )
            connection.execute(
                "INSERT INTO response_answers (response_id,question_id,text_value) "
                "VALUES (?,6,'Useful course content.')", (response,),
            )


def clear_submission(database):
    with sqlite3.connect(database) as connection:
        connection.execute(
            "DELETE FROM response_answers WHERE response_id IN "
            "(SELECT id FROM responses WHERE student_id=1 AND evaluation_id=1)"
        )
        connection.execute("DELETE FROM responses WHERE student_id=1 AND evaluation_id=1")


def measure_request(client, operation):
    path, role, expected = {
        "login": ("/api/auth/login", None, 200),
        "list": ("/api/evaluations", "student", 200),
        "questions": ("/api/evaluations/1/questions", "student", 200),
        "submission": ("/api/submissions", "student", 201),
        "feedback_api": ("/api/courses/1/feedback", "lecturer", 200),
        "feedback_html": ("/lecturer/feedback/1", "lecturer", 200),
        "logout": ("/api/auth/logout", "student", 200),
    }[operation]
    if role:
        with client.session_transaction() as session:
            session["user_id"] = 2 if role == "lecturer" else 1
            session["role"] = role
    request = {"method": "GET"}
    if operation == "login":
        request = {"method": "POST", "json": FIXTURE_CREDENTIALS}
    elif operation == "submission":
        request = {"method": "POST", "json": {
            "evaluation_id": 1,
            "answers": {str(n): {"rating_value": 3} for n in range(1, 6)},
        }}
    elif operation == "logout":
        request = {"method": "POST"}
    start = time.perf_counter_ns()
    response = client.open(path, **request)
    response.get_data()
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    assert response.status_code == expected, (operation, response.status_code)
    if operation == "login":
        assert response.get_json()["authenticated"] is True
    elif operation == "list":
        assert response.get_json()["count"] == 3
    elif operation == "submission":
        assert response.get_json()["status"] == "submitted"
    elif operation == "feedback_api":
        assert response.get_json()["completed_evaluations"] == 20
    elif operation == "logout":
        assert response.get_json() == {"authenticated": False}
        assert client.get("/api/auth/me").status_code == 401
    return elapsed_ms, response.status_code


def cookie_probe():
    with app_module.app.test_client() as client:
        assert client.post("/api/auth/login", json=FIXTURE_CREDENTIALS).status_code == 200
        cookie_name = app_module.app.config["SESSION_COOKIE_NAME"]
        saved = client.get_cookie(cookie_name)
        assert saved is not None
        assert client.post("/api/auth/logout").status_code == 200
        own_status = client.get("/api/auth/me").status_code
        with app_module.app.test_client() as copied_client:
            copied_client.set_cookie(cookie_name, saved.value)
            copied_status = copied_client.get("/api/auth/me").status_code
    return {"current_client_after_logout_status": own_status,
            "copied_pre_logout_cookie_after_logout_status": copied_status,
            "meaning": "Observation only; cookie revocation is not established. No cookie value exported."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 1 or args.warmups < 0:
        parser.error("samples must be positive and warmups non-negative")
    report = {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "application_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "application_sha256": hashlib.sha256((ROOT / "src/app.py").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "flask": version("Flask"),
                        "werkzeug": version("Werkzeug"), "sqlite": sqlite3.sqlite_version,
                        "os": platform.system(), "os_release": platform.release(),
                        "architecture": platform.machine(), "logical_cpus": os.cpu_count()},
        "protocol": {"clock": "time.perf_counter_ns", "unit": "milliseconds",
                     "interval": "Flask client.open through response.get_data; setup/verification excluded",
                     "load": "one process, sequential, temporary local SQLite; no network/browser",
                     "domain_clock": NOW.isoformat(), "samples_per_operation": args.samples,
                     "warmups_per_operation": args.warmups, "p95_method": "nearest rank",
                     "reference_budget_ms": 3000, "reference_comparison": "<=",
                     "acceptance_status": "NOT EVALUATED: local component diagnostic is not browser/deployed SLA"},
        "fixture": {"courses": 1, "evaluations": 3, "required_rating_questions": 5,
                    "optional_text_questions": 1, "baseline_submitted_responses": 20},
        "operations": {},
    }
    with tempfile.TemporaryDirectory(prefix="edusurvey-p0-timing-") as directory:
        database = Path(directory) / "timing.db"
        seed(database)
        with patch.object(app_module, "DATABASE", database), \
             patch.object(app_module, "datetime", FrozenDateTime), \
             patch.dict(app_module.app.config, {"TESTING": True, "SECRET_KEY": "timing-fixture-only"}):
            for operation in ("login", "list", "questions", "submission", "feedback_api", "feedback_html", "logout"):
                durations, statuses = [], []
                for index in range(args.warmups + args.samples):
                    with app_module.app.test_client() as client:
                        elapsed, status = measure_request(client, operation)
                        if operation == "submission":
                            clear_submission(database)
                    if index >= args.warmups:
                        durations.append(elapsed)
                        statuses.append(status)
                ordered = sorted(durations)
                report["operations"][operation] = {
                    "durations_ms": durations, "status_codes": sorted(set(statuses)),
                    "p50_ms": statistics.median(durations),
                    "p95_ms": ordered[math.ceil(len(ordered) * .95) - 1],
                    "max_ms": max(durations),
                    "all_within_reference_budget": max(durations) <= 3000,
                }
            report["logout_cookie_probe"] = cookie_probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for operation, result in report["operations"].items():
        print(f"{operation}: n={len(result['durations_ms'])} "
              f"p50={result['p50_ms']:.3f}ms p95={result['p95_ms']:.3f}ms max={result['max_ms']:.3f}ms")
    print("Cookie probe statuses:", report["logout_cookie_probe"]["current_client_after_logout_status"],
          report["logout_cookie_probe"]["copied_pre_logout_cookie_after_logout_status"])
    print("Diagnostic only; no browser/deployed acceptance claim. Report:", args.output)


if __name__ == "__main__":
    main()
