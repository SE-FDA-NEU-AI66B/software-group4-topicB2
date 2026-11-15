"""Backend audit cases BE-01–10: readiness, safe telemetry, ownership and backup."""

import json
import logging
import os
import sqlite3
import stat
from contextlib import closing
from datetime import UTC

import pytest
from flask import Flask

from src import app as app_module
from src.runtime import configure_runtime
from tools.backup_database import backup_database


@pytest.mark.parametrize("state", ["ready", "missing", "empty", "corrupt"])
def test_health_database_check(api_client, tmp_path, monkeypatch, state):
    """BE-01: real SQLite/schema check; missing DB must never be auto-created."""
    if state != "ready":
        path = tmp_path / f"{state}.db"
        if state == "empty":
            path.touch()
        elif state == "corrupt":
            path.write_text("not an sqlite database")
        monkeypatch.setattr(app_module, "DATABASE", path)
    response = api_client.get("/health")
    assert response.status_code == (200 if state == "ready" else 503)
    assert response.get_json() == ({"status": "ok", "database": "ok"} if state == "ready" else {"status": "unavailable", "database": "unavailable"})
    assert response.headers["Cache-Control"] == "no-store"
    if state == "missing":
        assert not path.exists()


def test_request_logs_exclude_user_input(api_client, caplog):
    """BE-02: raw path/query, credentials, cookies and answers stay out of telemetry."""
    with caplog.at_level(logging.INFO, logger=app_module.app.logger.name):
        api_client.post("/api/auth/login?token=PRIVATE_QUERY", json={"email": "PRIVATE_EMAIL", "password": "PRIVATE_CREDENTIAL"}, headers={"Cookie": "session=PRIVATE_COOKIE"})
        api_client.get("/unknown/PRIVATE_PATH?answer=PRIVATE_ANSWER")
    events = [json.loads(record.message) for record in caplog.records if record.message.startswith('{"duration_ms"')]
    assert len(events) == 2
    assert all(set(event) == {"event", "endpoint", "method", "status", "duration_ms"} for event in events)
    assert events[1]["endpoint"] == "unmatched"
    assert all(event["duration_ms"] >= 0 for event in events)
    assert "PRIVATE_" not in caplog.text


@pytest.mark.parametrize("endpoint", ["feedback/topics", "feedback/topics/ranking", "statistics"])
@pytest.mark.parametrize("identity,status", [(None, 401), ("student", 403), ("administrator", 403), ("unassigned", 403), ("lecturer", 200)])
def test_feedback_aggregate_permissions(api_client, endpoint, identity, status):
    """BE-03: aggregated feedback is private to the course's assigned lecturer."""
    if identity:
        with api_client.session_transaction() as session:
            session["user_id"] = 1 if identity == "student" else 3 if identity in ("administrator", "unassigned") else 2
            session["role"] = "lecturer" if identity == "unassigned" else identity
    response = api_client.get(f"/api/evaluations/1/{endpoint}")
    assert response.status_code == status
    if status != 200:
        assert set(response.get_json()) == {"error"}
        assert b"The course content was very useful" not in response.data


def test_missing_database_is_safe_503(api_client, monkeypatch, tmp_path, caplog):
    """BE-04: request errors disclose neither database location nor submitted input."""
    database = tmp_path / "PRIVATE_DATABASE.db"
    monkeypatch.setattr(app_module, "DATABASE", database)
    response = api_client.post("/api/auth/login", json={"email": "PRIVATE_EMAIL", "password": "PRIVATE_CREDENTIAL"})
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "PRIVATE_" not in response.text + caplog.text
    assert not database.exists()


@pytest.mark.parametrize("secret,path,valid", [(None, "/data/app.db", False), ("short", "/data/app.db", False), ("s" * 40, None, False), ("s" * 40, "relative.db", False), ("s" * 40, "/data/app.db", True)])
def test_production_config_requires_explicit_secrets_and_storage(monkeypatch, tmp_path, secret, path, valid):
    """BE-05: production refuses implicit demo config; HTTPS session cookie required."""
    monkeypatch.setenv("EDUSURVEY_ENV", "production")
    if path == "/data/app.db":
        path = str(tmp_path / "app.db")  # A real absolute path on Windows and Linux.
    for key, value in (("EDUSURVEY_SECRET_KEY", secret), ("EDUSURVEY_DATABASE", path)):
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    app = Flask(__name__)
    if not valid:
        with pytest.raises(RuntimeError):
            configure_runtime(app, "default.db")
    else:
        configure_runtime(app, "default.db")
        assert app.config["SESSION_COOKIE_SECURE"] is True
        assert app.config["SESSION_COOKIE_HTTPONLY"] is True
        assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_database_transaction_closes_and_rolls_back(api_client):
    """BE-06: runtime enforces foreign keys and rolls back failed transactions."""
    with pytest.raises(sqlite3.IntegrityError), app_module.get_db_connection() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        connection.execute("INSERT INTO courses (course_code, course_name) VALUES ('ROLLBACK', 'rollback')")
        connection.execute("INSERT INTO course_enrollments (student_id, course_id) VALUES (99999, 1)")
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
    with app_module.get_db_connection() as check:
        assert check.execute("SELECT COUNT(*) FROM courses WHERE course_code='ROLLBACK'").fetchone()[0] == 0


def test_online_backup_and_restore_round_trip(api_client, tmp_path, monkeypatch):
    """BE-07: backup survives new source changes; a restored copy has original data."""
    source = app_module.DATABASE
    backup = tmp_path / "snapshot.db"
    restored = tmp_path / "restored.db"
    original_open = os.open
    creation_modes = []

    def recorded_open(path, flags, mode=0o777):
        creation_modes.append(mode)
        return original_open(path, flags, mode)

    monkeypatch.setattr(os, "open", recorded_open)
    backup_database(source, backup)
    assert creation_modes == [0o600]
    mode = backup.stat().st_mode
    if os.name == "nt":
        # Windows exposes read/write attributes, not POSIX group/other permissions.
        # This does not claim to audit Windows ACLs.
        assert mode & stat.S_IREAD and mode & stat.S_IWRITE
    else:
        assert mode & 0o077 == 0
    with app_module.get_db_connection() as connection:
        connection.execute("UPDATE courses SET course_name='CHANGED' WHERE id=1")
    backup_database(backup, restored)
    with closing(sqlite3.connect(restored)) as connection:
        assert connection.execute("SELECT course_name FROM courses WHERE id=1").fetchone()[0] == "Test Course"
    with pytest.raises(FileExistsError):
        backup_database(source, backup)


def test_backup_missing_source_creates_no_output(tmp_path):
    """BE-08: a missing mount cannot silently produce a new empty backup."""
    source, target = tmp_path / "missing.db", tmp_path / "target.db"
    with pytest.raises(sqlite3.OperationalError):
        backup_database(source, target)
    assert not source.exists() and not target.exists()


def test_production_initializer_refuses_reset(api_client, monkeypatch):
    """BE-09: initial seed script is not a production migration/reset command."""
    from src import init_db

    monkeypatch.setenv("EDUSURVEY_ENV", "production")
    monkeypatch.setattr(init_db, "DB_PATH", app_module.DATABASE)
    with pytest.raises(RuntimeError, match="Refusing"):
        init_db.initialize_database()
    assert api_client.get("/health").status_code == 200


def test_unexpected_errors_are_sanitized(api_client, monkeypatch, caplog):
    """BE-10: unexpected exceptions are observable without logging private values."""
    def fail():
        raise RuntimeError("PRIVATE_EXCEPTION_INPUT")

    monkeypatch.setitem(app_module.app.view_functions, "home", fail)
    response = api_client.get("/")
    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "INTERNAL_ERROR"
    assert "PRIVATE_" not in response.text + caplog.text
    assert "RuntimeError" in caplog.text


def test_fresh_m5_demo_has_student_work_and_lecturer_feedback(tmp_path, monkeypatch, fixed_app_clock):
    """BE-11: opt-in new demo DB offers a fresh student action and submitted feedback."""
    from datetime import timedelta

    from src import init_db

    database = tmp_path / "demo.db"
    monkeypatch.setattr(init_db, "DB_PATH", database)
    monkeypatch.setattr(init_db, "DB_DIR", tmp_path)
    monkeypatch.setenv("EDUSURVEY_ENV", "production")
    init_db.initialize_database(m5_demo=True, now=fixed_app_clock)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM responses WHERE student_id=1 AND evaluation_id=1").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM responses WHERE evaluation_id=3 AND status='submitted'").fetchone()[0] == 1
        expected = (fixed_app_clock + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        assert connection.execute("SELECT DISTINCT deadline FROM evaluations WHERE status='open'").fetchall() == [(expected,)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(RuntimeError, match="Refusing"):
        init_db.initialize_database(m5_demo=True, now=fixed_app_clock)


@pytest.mark.parametrize("seconds,status", [(86399, "Due soon"), (86400, "Active"), (86401, "Active"), (0, "Closed")])
def test_offset_deadlines_consistent_across_p0(api_client, monkeypatch, seconds, status):
    """BE-12: list, questions and submit agree on +07:00 boundaries at a fixed instant."""
    from datetime import datetime, timedelta, timezone

    instant = datetime(2026, 11, 4, 12, tzinfo=UTC)

    class UtcClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    monkeypatch.setattr(app_module, "datetime", UtcClock)
    deadline = (instant + timedelta(seconds=seconds)).astimezone(timezone(timedelta(hours=7))).isoformat()
    with app_module.get_db_connection() as connection:
        connection.execute("DELETE FROM response_answers")
        connection.execute("DELETE FROM responses")
        connection.execute("UPDATE evaluations SET deadline=? WHERE id=1", (deadline,))
    with api_client.session_transaction() as session:
        session["user_id"], session["role"] = 1, "student"
    response = api_client.get("/api/evaluations")
    assert response.status_code == 200
    assert response.get_json()["evaluations"][0]["survey_status"] == status
    assert api_client.get("/api/evaluations/1/questions").status_code == (400 if seconds == 0 else 200)
    response = api_client.post("/api/submissions", json={"evaluation_id": 1, "answers": {"1": {"rating_value": 5}}})
    assert response.status_code == (400 if seconds == 0 else 201)
