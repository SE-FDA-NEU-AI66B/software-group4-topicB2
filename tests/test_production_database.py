"""#204 / parent #200: new-only provisioning, demo persistence and isolated recovery."""

import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from threading import Thread

import pytest
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from src import app as app_module
from src import init_db
from tools.backup_database import backup_database
from tools.verify_database import verify_database


@pytest.fixture
def demo_database(tmp_path, monkeypatch, fixed_app_clock):
    database = tmp_path / "demo.db"
    monkeypatch.setenv("EDUSURVEY_ENV", "production")
    monkeypatch.setenv("EDUSURVEY_DATABASE", str(database))
    monkeypatch.setenv("EDUSURVEY_SECRET_KEY", "synthetic-secret-for-isolated-tests-204")
    monkeypatch.setattr(init_db, "DB_PATH", database)
    monkeypatch.setattr(init_db, "DB_DIR", tmp_path)
    init_db.initialize_database(m5_demo=True, now=fixed_app_clock)
    monkeypatch.setattr(app_module, "DATABASE", database)
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "synthetic-test-session")
    # Local loopback HTTP only; production HTTPS uses Secure cookies.
    monkeypatch.setitem(app_module.app.config, "SESSION_COOKIE_SECURE", False)
    return database


@pytest.mark.parametrize("email,role,landing", [
    ("student1@edusurvey.edu", "student", "/evaluations"),
    ("lecturer1@edusurvey.edu", "lecturer", "/lecturer/feedback"),
    ("admin@edusurvey.edu", "administrator", "/account"),
])
def test_demo_roles_have_usable_landing(demo_database, email, role, landing):
    with app_module.app.test_client() as client:
        response = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
        assert response.status_code == 200
        assert response.get_json()["user"]["role"] == role
        assert client.get(landing).status_code == 200
        if role == "student":
            evaluations = client.get("/api/evaluations").get_json()["evaluations"]
            assert any(e["id"] == 1 and e["survey_status"] == "Active" for e in evaluations)
        if role == "lecturer":
            feedback = client.get("/api/courses/2/feedback").get_json()
            assert feedback["completed_evaluations"] > 0


@pytest.mark.parametrize("environment", ["production", "development"])
def test_initializer_preserves_existing_file(demo_database, monkeypatch, environment):
    before = demo_database.read_bytes()
    monkeypatch.setenv("EDUSURVEY_ENV", environment)
    with pytest.raises(RuntimeError, match="Refusing to reset"):
        init_db.initialize_database(m5_demo=True)
    assert demo_database.read_bytes() == before


def test_failed_initialization_leaves_no_published_database(tmp_path, monkeypatch):
    database = tmp_path / "failed.db"
    monkeypatch.setattr(init_db, "DB_PATH", database)

    def fail(*args):
        raise RuntimeError("synthetic seed failure")

    monkeypatch.setattr(init_db, "generate_password_hash", fail)
    with pytest.raises(RuntimeError, match="synthetic seed failure"):
        init_db.initialize_database(m5_demo=True)
    assert not database.exists()
    assert list(tmp_path.iterdir()) == []


def test_initializer_never_overwrites_concurrent_winner(tmp_path, monkeypatch, fixed_app_clock):
    database = tmp_path / "winner.db"
    monkeypatch.setattr(init_db, "DB_PATH", database)
    original_link = os.link

    def concurrent_publish(source, destination):
        # Simulate a second process publishing after our initial existence check.
        destination.write_bytes(b"concurrent winner must survive")
        original_link(source, destination)

    monkeypatch.setattr(init_db.os, "link", concurrent_publish)
    with pytest.raises(FileExistsError):
        init_db.initialize_database(m5_demo=True, now=fixed_app_clock)
    assert database.read_bytes() == b"concurrent winner must survive"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["winner.db"]


def test_platform_environment_and_new_process_read(demo_database):
    result = subprocess.run([sys.executable, "-c", """
import os
from pathlib import Path
from src.app import DATABASE, app
assert DATABASE == Path(os.environ['EDUSURVEY_DATABASE'])
assert app.config['SESSION_COOKIE_SECURE'] is True
with app.test_client() as client:
    assert client.get('/health').status_code == 200
print('production environment and existing storage verified')
"""], capture_output=True, text=True, check=True)
    assert "existing storage verified" in result.stdout


def test_actual_backup_restore_preserves_snapshot(demo_database, tmp_path):
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    with app_module.app.test_client() as client:
        assert client.post("/api/auth/login", json={
            "email": "student1@edusurvey.edu", "password": "Password123!",
        }).status_code == 200
        assert client.post("/api/submissions", json={
            "evaluation_id": 1,
            "answers": {"1": {"rating_value": 5}, "2": {"rating_value": 4},
                        "3": {"text_value": "Created before the backup"}},
        }).status_code == 201
    before = verify_database(demo_database)
    backup_database(demo_database, backup)
    with closing(sqlite3.connect(demo_database)) as db, db:
        db.execute("UPDATE courses SET course_name='After backup' WHERE id=1")
    backup_database(backup, restored)
    result = verify_database(backup, compare=restored)
    assert result["comparison"] == "equal"
    assert result["table_counts"] == before["table_counts"]
    with pytest.raises(ValueError, match="differs"):
        verify_database(demo_database, compare=restored)
    with closing(sqlite3.connect(restored)) as db:
        assert db.execute("SELECT course_name FROM courses WHERE id=1").fetchone()[0] == "Software Engineering"
    # Restored database is usable through the same real app, not only raw SQL.
    original_database = app_module.DATABASE
    try:
        app_module.DATABASE = restored
        with app_module.app.test_client() as client:
            assert client.get("/health").status_code == 200
            assert client.post("/api/auth/login", json={
                "email": "student1@edusurvey.edu", "password": "Password123!",
            }).status_code == 200
            evaluations = client.get("/api/evaluations").get_json()["evaluations"]
            assert any(e["id"] == 1 and e["survey_status"] == "Completed" for e in evaluations)
            assert client.post("/api/auth/login", json={
                "email": "lecturer1@edusurvey.edu", "password": "Password123!",
            }).status_code == 200
            assert client.get("/api/courses/1/feedback").get_json()["completed_evaluations"] == 1
            assert client.get("/api/courses/2/feedback").get_json()["completed_evaluations"] > 0
    finally:
        app_module.DATABASE = original_database
    with pytest.raises(FileExistsError):
        backup_database(demo_database, restored)
    assert verify_database(backup, compare=restored)["comparison"] == "equal"


def test_created_record_survives_new_process(demo_database):
    with app_module.app.test_client() as client:
        client.post("/api/auth/login", json={"email": "student1@edusurvey.edu", "password": "Password123!"})
        assert client.post("/api/submissions", json={
            "evaluation_id": 1, "answers": {"1": {"rating_value": 5}, "2": {"rating_value": 4}},
        }).status_code == 201
    result = subprocess.run([sys.executable, "-c", """
from src.app import app, get_db_connection
with get_db_connection() as db:
    assert db.execute("SELECT COUNT(*) FROM responses WHERE evaluation_id=1 AND student_id=1 AND status='submitted'").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM response_answers a JOIN responses r ON r.id=a.response_id WHERE r.evaluation_id=1 AND r.student_id=1").fetchone()[0] == 2
with app.test_client() as client:
    assert client.get('/health').status_code == 200
print('committed submission survived a new application process')
"""], capture_output=True, text=True, check=True)
    assert "survived a new application process" in result.stdout


@pytest.mark.parametrize("state", ["missing", "corrupt", "foreign-key"])
def test_backup_rejects_invalid_source_without_output(demo_database, tmp_path, state):
    source = tmp_path / "source.db"
    target = tmp_path / "rejected.db"
    if state == "corrupt":
        source.write_bytes(b"not SQLite")
    if state == "foreign-key":
        backup_database(demo_database, source)
        with closing(sqlite3.connect(source)) as db, db:
            db.execute("INSERT INTO course_enrollments (student_id,course_id) VALUES (9999,1)")
    before = source.read_bytes() if source.exists() else None
    with pytest.raises(sqlite3.Error):
        backup_database(source, target)
    assert not target.exists()
    assert (source.read_bytes() if source.exists() else None) == before


def test_failed_backup_removes_only_its_partial_output(demo_database, tmp_path, monkeypatch):
    target = tmp_path / "partial.db"
    before = demo_database.read_bytes()
    original_connect = sqlite3.connect

    class FailedCopy(sqlite3.Connection):
        def backup(self, destination, **kwargs):
            destination.execute("CREATE TABLE incomplete (id INTEGER)")
            raise sqlite3.OperationalError("synthetic backup failure")

    def connect(database, **kwargs):
        if kwargs.get("uri"):
            kwargs["factory"] = FailedCopy
        return original_connect(database, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    with pytest.raises(sqlite3.OperationalError, match="synthetic backup failure"):
        backup_database(demo_database, target)
    assert not target.exists()
    assert demo_database.read_bytes() == before


def test_readonly_verification_never_creates_missing_file(tmp_path):
    missing = tmp_path / "missing.db"
    with pytest.raises(sqlite3.OperationalError):
        verify_database(missing)
    assert not missing.exists()


def test_seeded_submission_survives_browser_reload(demo_database):
    """Actual Chromium reload against new canonical M5 seed and temporary SQLite."""
    server = make_server("127.0.0.1", 0, app_module.app, threaded=True)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, **(
                {"executable_path": os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]}
                if os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") else {}
            ))
            try:
                page = browser.new_page()
                url = f"http://127.0.0.1:{server.server_port}"
                page.goto(url + "/login")
                page.get_by_label("Email", exact=False).fill("student1@edusurvey.edu")
                page.locator("#password").fill("Password123!")
                page.get_by_role("button", name="Sign in", exact=True).click()
                expect(page).to_have_url(url + "/evaluations")
                page.locator('a[href="/evaluations/1/complete"]').click()
                ratings = page.locator('input[type="radio"][value="5"]')
                # Questions load via fetch; Locator.all() does not wait for them.
                expect(ratings).to_have_count(2)
                for rating in ratings.all():
                    rating.focus()
                    page.keyboard.press("Space")
                    expect(rating).to_be_checked()
                page.locator("textarea").fill("Synthetic persistence check #204")
                page.locator("#reviewButton").click()
                page.get_by_role("button", name="Submit evaluation", exact=True).click()
                expect(page.locator("#submissionSuccess")).to_be_visible()
                page.reload(wait_until="domcontentloaded")
                expect(page.locator("#submissionSuccess")).to_be_visible()
                assert page.request.get(url + "/api/evaluations").ok
                with closing(sqlite3.connect(demo_database)) as db:
                    assert db.execute("SELECT COUNT(*) FROM responses WHERE student_id=1 AND evaluation_id=1 AND status='submitted'").fetchone()[0] == 1
                    assert db.execute("SELECT COUNT(*) FROM response_answers a JOIN responses r ON r.id=a.response_id WHERE r.student_id=1 AND r.evaluation_id=1").fetchone()[0] == 3
            finally:
                browser.close()
    finally:
        server.shutdown()
        worker.join(timeout=5)
        server.server_close()
