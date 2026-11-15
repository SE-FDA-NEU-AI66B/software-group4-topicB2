"""Measure actual loopback creation HTTP latency; never a deployed/browser SLA."""

import argparse
import hashlib
import json
import math
import os
import platform
import secrets
import sqlite3
import statistics
import subprocess
import tempfile
import time
import urllib.request
from contextlib import closing
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import WSGIRequestHandler, make_server

from src import app as module
from tools.measure_p0_latency import FrozenDateTime, seed


class QuietRequests(WSGIRequestHandler):
    def log(self, *args, **kwargs):
        pass


def measure(samples, warmups):
    original_database, original_datetime = module.DATABASE, module.datetime
    original_config = module.app.config.copy()
    try:
        with tempfile.TemporaryDirectory(prefix="creation-latency-") as directory:
            database = Path(directory) / "latency.db"
            # Reuse the profile but explicitly close its legacy seed connection.
            # sqlite3's transaction context alone does not close the handle.
            connections = []
            original_connect = sqlite3.connect

            def seed_connection(*args, **kwargs):
                connection = original_connect(*args, **kwargs)
                connections.append(connection)
                return connection

            try:
                with patch("tools.measure_p0_latency.sqlite3.connect", seed_connection):
                    seed(database)
            finally:
                for connection in connections:
                    connection.close()
            module.DATABASE, module.datetime = database, FrozenDateTime
            module.app.config.update(TESTING=True, SECRET_KEY=secrets.token_hex(32), SESSION_COOKIE_SECURE=False)
            with module.app.test_client() as client:
                with client.session_transaction() as session:
                    session["user_id"], session["role"] = 2, "lecturer"
                cookie = client.get_cookie("session").value
            server = make_server("127.0.0.1", 0, module.app, threaded=True, request_handler=QuietRequests)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            durations = []
            try:
                for index in range(samples + warmups):
                    payload = {"course_id": 1, "title": f"Measured evaluation {index}",
                               "deadline": "2026-11-06T12:00:00+00:00",
                               "questions": [{"question_text": f"Question {n}",
                                              "question_type": "rating" if n < 4 else "text",
                                              "is_required": n < 4} for n in range(1, 6)]}
                    request = urllib.request.Request(
                        f"http://127.0.0.1:{server.server_port}/api/evaluations",
                        data=json.dumps(payload).encode(),
                        headers={"Content-Type": "application/json", "Cookie": "session=" + cookie}, method="POST")
                    start = time.perf_counter_ns()
                    with urllib.request.urlopen(request, timeout=10) as response:
                        result = json.load(response)
                        status = response.status
                    elapsed = (time.perf_counter_ns() - start) / 1_000_000
                    assert status == 201 and len(result["questions"]) == result["questions_created"] == 5
                    # Verify committed data after timing, not inside the measured interval.
                    with closing(sqlite3.connect(database)) as db:
                        assert db.execute("SELECT course_id,created_by FROM evaluations WHERE id=?",
                                          (result["evaluation_id"],)).fetchone() == (1, 2)
                        assert db.execute("SELECT COUNT(*) FROM questions WHERE evaluation_id=?",
                                          (result["evaluation_id"],)).fetchone()[0] == 5
                    if index >= warmups:
                        durations.append(elapsed)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
            return {"captured_at": datetime.now(UTC).isoformat(),
                    "base_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                    "source_state": "base revision plus #198 working-tree changes; exact source hashes below",
                    "working_tree_source_sha256": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                                                   for name in ("src/app.py", "src/schema.sql", "tools/measure_creation_latency.py")},
                    "environment": {"os": platform.system(), "python": platform.python_version(),
                                    "flask": version("flask"), "werkzeug": version("werkzeug"),
                                    "machine": platform.machine(), "logical_cpus": os.cpu_count()},
                    "profile": {"transport": "loopback HTTP / Werkzeug threaded WSGI, not production",
                                "concurrency": 1, "seed": "existing P0 seed: 22 users, 1 course, 3 evaluations, 20 responses",
                                "questions_per_creation": 5, "warmups": warmups, "samples": samples,
                                "auth": "preauthenticated synthetic lecturer; login excluded",
                                "load": "sequential warmed requests; background OS load not controlled",
                                "interval": "before HTTP POST to fully consumed JSON confirmation after commit",
                                "excluded": "DB seeding, payload/cookie setup, post-request SQL verification, TLS and browser rendering"},
                    "durations_ms": durations, "p50_ms": statistics.median(durations),
                    "p95_ms": sorted(durations)[math.ceil(0.95 * len(durations)) - 1], "max_ms": max(durations),
                    "observed_http": 201, "all_within_reference_3000_ms": all(value <= 3000 for value in durations),
                    "deployed_browser_acceptance": "NOT VERIFIED; requires #197 and actual release profile"}
    finally:
        module.DATABASE, module.datetime = original_database, original_datetime
        module.app.config.clear()
        module.app.config.update(original_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/198/creation-latency.json"))
    args = parser.parse_args()
    if args.samples < 1 or args.warmups < 0:
        parser.error("Use samples >= 1 and warmups >= 0.")
    report = measure(args.samples, args.warmups)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("p50_ms", "p95_ms", "max_ms", "all_within_reference_3000_ms")}))
