"""Capture #203 local candidates from pinned git snapshots and synthetic data.

These images establish code differences, not M3 feedback or release verification.
"""

import argparse
import hashlib
import io
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import tarfile
from contextlib import closing
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread


def worker(source, output, revision, scenario, phase):
    sys.path.insert(0, str(source))
    from playwright.sync_api import expect, sync_playwright
    from werkzeug.serving import make_server

    from src import app as module

    instant = datetime(2026, 11, 4, 12)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant if tz is None else instant.replace(tzinfo=tz)

    module.datetime = FixedDateTime
    database = source / "synthetic.db"
    with closing(sqlite3.connect(database)) as db, db:
        db.executescript((source / "src/schema.sql").read_text(encoding="utf-8"))
        db.executemany(
            "INSERT INTO users (id,email,password_hash,full_name,role,created_at) "
            "VALUES (?,?, 'unused-no-login',?,?,?)",
            [(1, "student@example.test", "Demo Student", "student", instant.isoformat()),
             (2, "lecturer@example.test", "Demo Lecturer", "lecturer", instant.isoformat())],
        )
        db.executemany(
            "INSERT INTO courses (id,course_code,course_name,created_at) VALUES (?,?,?,?)",
            [(1, "DEMO101", "Demo Course", instant.isoformat()),
             (2, "PRIVATE202", "Hidden Course", instant.isoformat())],
        )
        db.execute("INSERT INTO course_enrollments (student_id,course_id,enrolled_at) VALUES (1,1,?)", (instant.isoformat(),))
        db.execute("INSERT INTO course_lecturers (lecturer_id,course_id,assigned_at) VALUES (2,1,?)", (instant.isoformat(),))
        db.executemany(
            "INSERT INTO evaluations (id,course_id,created_by,title,deadline,status,created_at) "
            "VALUES (?,?,2,?,'2026-11-06T12:00:00','open',?)",
            [(1, 1, "Demo Course Evaluation", instant.isoformat()),
             (2, 2, "Hidden Evaluation", instant.isoformat())],
        )
    module.DATABASE = database
    module.app.config.update(TESTING=True, SECRET_KEY=secrets.token_hex(32))
    user_id, role, route = (1, "student", "/evaluations") if scenario == "student" else (2, "lecturer", "/lecturer/feedback/2")
    with module.app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = user_id
            session["role"] = role
        cookie = client.get_cookie("session").value
    server = make_server("127.0.0.1", 0, module.app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    records = []
    try:
        with sync_playwright() as playwright:
            options = {"headless": True}
            if executable := os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"):
                options["executable_path"] = executable
            browser = playwright.chromium.launch(**options)
            try:
                for label, width, height in (("laptop", 1440, 900), ("phone", 390, 844)):
                    context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
                    # Block external fonts/requests consistently in both snapshots.
                    context.route("**/*", lambda request: request.continue_() if request.request.url.startswith(url) else request.abort())
                    context.add_cookies([{"name": "session", "value": cookie, "url": url}])
                    page = context.new_page()
                    response = page.goto(url + route, wait_until="networkidle")
                    expected_status = 200 if scenario == "student" else 403
                    assert response.status == expected_status
                    if scenario == "student":
                        expect(page.get_by_text("Demo Course Evaluation", exact=True)).to_be_visible()
                        assert page.get_by_role("button", name="Sign out", exact=True).count() == (1 if phase == "after" else 0)
                    elif phase == "after":
                        expect(page.get_by_role("alert")).to_be_visible()
                        expect(page.get_by_role("link", name="Return to assigned evaluations")).to_be_visible()
                    else:
                        expect(page.get_by_role("alert")).to_be_visible()
                        assert page.get_by_role("link", name="Return to assigned evaluations").count() == 0
                    assert "Hidden Evaluation" not in page.content()
                    file = output / f"{scenario}-{phase}-{label}.png"
                    page.screenshot(path=str(file), full_page=True)
                    records.append({"file": file.name, "commit": revision, "route": route,
                                    "status": response.status, "viewport": [width, height],
                                    "horizontal_overflow": page.evaluate("document.documentElement.scrollWidth > innerWidth"),
                                    "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
                    if phase == "after":
                        if scenario == "student":
                            page.get_by_role("button", name="Sign out", exact=True).click()
                            expect(page).to_have_url(url + "/login")
                            assert page.request.get(url + "/api/auth/me").status == 401
                        else:
                            page.get_by_role("link", name="Return to assigned evaluations").click()
                            expect(page).to_have_url(url + "/lecturer/feedback")
                            expect(page.get_by_role("link", name="Review feedback:", exact=False)).to_have_count(1)
                    context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    (output / f"{scenario}-{phase}.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/203"))
    parser.add_argument("--after", default="dff0de8")
    parser.add_argument("--worker", nargs=4, metavar=("SOURCE", "REVISION", "SCENARIO", "PHASE"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.worker:
        source, revision, scenario, phase = args.worker
        worker(Path(source), output, revision, scenario, phase)
        return
    jobs = [("student", "before", "5a52af6"), ("lecturer", "before", "2cb2b05"),
            ("student", "after", args.after), ("lecturer", "after", args.after)]
    for scenario, phase, ref in jobs:
        revision = subprocess.check_output(["git", "rev-parse", ref], text=True).strip()
        with TemporaryDirectory(prefix="ui-203-") as directory:
            source = Path(directory)
            archive = subprocess.check_output(["git", "archive", revision, "src"])
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(source, filter="data")
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--output", str(output),
                            "--worker", str(source), revision, scenario, phase], check=True)
        print(f"Captured {scenario} {phase} at {revision}", flush=True)


if __name__ == "__main__":
    main()
