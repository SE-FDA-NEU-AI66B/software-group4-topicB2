"""US12 #195: database-authorized management, current permissions and settings."""

import sqlite3
from contextlib import closing
from datetime import UTC

import pytest

from src import app as app_module
from src.admin import AREA_DENIED, SUPPORT_DEFAULT
from tools.migrate_us12_settings import migrate


@pytest.fixture
def admin_client(api_client):
    authenticate(api_client, 3, "administrator")
    return api_client


def authenticate(client, user_id, role):
    with client.session_transaction() as session:
        session["user_id"], session["role"] = user_id, role


def snapshot():
    with closing(sqlite3.connect(app_module.DATABASE)) as db:
        return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
                for table in ("users", "system_settings", "courses", "course_enrollments", "evaluations")}


OPERATIONS = [
    ("GET", "/api/admin", None), ("GET", "/api/admin/users", None),
    ("PATCH", "/api/admin/users/1/role", {"role": "administrator"}),
    ("GET", "/api/admin/settings", None),
    ("PUT", "/api/admin/settings/support_contact", {"value": "Forbidden update"}),
    ("PUT", "/api/evaluations/1/deadline", {"deadline": "2099-01-01T00:00:00"}),
]


@pytest.mark.parametrize("user_id", [1, 2], ids=["student", "lecturer"])
@pytest.mark.parametrize("method,url,data", OPERATIONS, ids=["area", "users", "role", "settings", "setting-write", "deadline"])
def test_admin_denies_other_roles(api_client, user_id, method, url, data):
    # Even a stale/forged administrator role in a correctly signed test session
    # cannot override the authenticated account's actual database role.
    authenticate(api_client, user_id, "administrator")
    before = snapshot()
    response = api_client.open(url + "?user_id=3&role=administrator", method=method, json=data)
    assert response.status_code == 403
    assert response.get_json()["error"]["message"] == AREA_DENIED
    assert snapshot() == before


@pytest.mark.parametrize("method,url,data", OPERATIONS, ids=["area", "users", "role", "settings", "setting-write", "deadline"])
def test_admin_requires_login(api_client, method, url, data):
    before = snapshot()
    response = api_client.open(url, method=method, json=data)
    assert response.status_code == 401
    assert snapshot() == before


def test_admin_reads_minimal_user_fields(admin_client):
    assert admin_client.get("/api/admin").status_code == 200
    response = admin_client.get("/api/admin/users")
    assert response.status_code == 200
    assert len(response.get_json()["users"]) == 3
    assert all(set(user) == {"id", "email", "full_name", "role"} for user in response.get_json()["users"])
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("role", ["student", "lecturer", "administrator"])
def test_admin_role_update_changes_existing_session(admin_client, role):
    target = app_module.app.test_client()
    authenticate(target, 1, "student")
    before = snapshot()
    response = admin_client.patch("/api/admin/users/1/role", json={"role": role})
    assert response.status_code == 200
    assert response.get_json()["user"] == {"id": 1, "role": role}
    after = snapshot()
    assert after["users"][0][4] == role
    assert after["users"][1:] == before["users"][1:]
    for table in ("courses", "course_enrollments", "evaluations", "system_settings"):
        assert after[table] == before[table]
    assert target.get("/api/auth/me").get_json()["user"]["role"] == role
    assert target.get("/api/evaluations").status_code == (200 if role == "student" else 403)
    assert target.get("/api/admin/users").status_code == (200 if role == "administrator" else 403)
    assert target.get("/lecturer/feedback").status_code == (200 if role == "lecturer" else 403)


def test_demotion_revokes_existing_admin_and_self_session(admin_client):
    target = app_module.app.test_client()
    authenticate(target, 3, "administrator")
    assert admin_client.patch("/api/admin/users/3/role", json={"role": "student"}).status_code == 200
    for client in (admin_client, target):
        response = client.put("/api/admin/settings/support_contact", json={"value": "Cannot save"})
        assert response.status_code == 403 and response.get_json()["error"]["message"] == AREA_DENIED


@pytest.mark.parametrize("payload", [{}, [], {"role": "admin"}, {"role": "Student"}, {"role": True},
                                     {"role": None}, {"role": ["administrator"]}, {"role": "student", "user_id": 3},
                                     {"role": "student'; DROP TABLE users; --"}])
def test_invalid_role_update_has_no_writes(admin_client, payload):
    before = snapshot()
    assert admin_client.patch("/api/admin/users/1/role", json=payload).status_code == 400
    assert snapshot() == before


def test_missing_target_and_deleted_actor_are_rejected(admin_client):
    before = snapshot()
    assert admin_client.patch("/api/admin/users/999/role", json={"role": "student"}).status_code == 404
    assert snapshot() == before
    with closing(sqlite3.connect(app_module.DATABASE)) as db, db:
        db.execute("DELETE FROM users WHERE id=3")
    assert admin_client.get("/api/admin/users").status_code == 401
    with admin_client.session_transaction() as session:
        assert "user_id" not in session


@pytest.mark.parametrize("length", [1, 200])
def test_support_contact_persists_and_applies(admin_client, fixed_app_clock, length):
    assert admin_client.get("/api/admin/settings").get_json()["settings"][0]["value"] == SUPPORT_DEFAULT
    value = "a" * length
    before = snapshot()
    response = admin_client.put("/api/admin/settings/support_contact", json={"value": f"  {value}  "})
    assert response.status_code == 200
    assert response.get_json()["setting"]["value"] == value
    timestamp = fixed_app_clock.replace(tzinfo=UTC).isoformat()
    assert response.get_json()["setting"]["updated_at"] == timestamp
    with closing(sqlite3.connect(app_module.DATABASE)) as db:
        assert db.execute("SELECT value,updated_by,updated_at FROM system_settings").fetchone() == (
            value, 3, timestamp)
    assert admin_client.get("/api/admin/settings").get_json()["settings"][0]["value"] == value
    for route in ("/", "/login"):
        assert value in app_module.app.test_client().get(route).get_data(as_text=True)
    for table in ("users", "courses", "course_enrollments", "evaluations"):
        assert snapshot()[table] == before[table]


@pytest.mark.parametrize("value", ["", "   ", "a" * 201, 1, True, None, [], "bad\ncontact", "bad\x00contact"])
def test_invalid_setting_has_no_writes(admin_client, value):
    before = snapshot()
    assert admin_client.put("/api/admin/settings/support_contact", json={"value": value}).status_code == 400
    assert snapshot() == before


def test_setting_catalog_strict_and_html_is_escaped(admin_client):
    before = snapshot()
    assert admin_client.put("/api/admin/settings/unknown", json={"value": "x"}).status_code == 400
    assert admin_client.put("/api/admin/settings/support_contact", json={"value": "x", "role": "administrator"}).status_code == 400
    assert snapshot() == before
    assert admin_client.put("/api/admin/settings/support_contact", json={"value": "<script>alert(1)</script>"}).status_code == 200
    html = admin_client.get("/login").get_data(as_text=True)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_old_database_migration_is_additive_and_repeatable(admin_client):
    original = snapshot()
    with closing(sqlite3.connect(app_module.DATABASE)) as db, db:
        db.execute("DROP TABLE system_settings")
    assert admin_client.get("/login").status_code == 200
    before_users = snapshot_without_settings()
    response = admin_client.put("/api/admin/settings/support_contact", json={"value": "Call support"})
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "SETTINGS_NOT_INITIALIZED"
    migrate(app_module.DATABASE)
    assert admin_client.put("/api/admin/settings/support_contact", json={"value": "Call support"}).status_code == 200
    after = snapshot()
    migrate(app_module.DATABASE)
    assert snapshot() == after
    assert snapshot_without_settings() == before_users
    for table in ("users", "courses", "course_enrollments", "evaluations"):
        assert snapshot()[table] == original[table]


def snapshot_without_settings():
    with closing(sqlite3.connect(app_module.DATABASE)) as db:
        return db.execute("SELECT * FROM users ORDER BY id").fetchall()


def test_migration_missing_database_creates_nothing(tmp_path):
    path = tmp_path / "missing.db"
    with pytest.raises(sqlite3.OperationalError):
        migrate(path)
    assert not path.exists()


@pytest.mark.parametrize("method,url,data", [OPERATIONS[2], OPERATIONS[4]], ids=["role", "setting"])
def test_admin_rechecked_inside_write_transaction(admin_client, monkeypatch, method, url, data):
    original_connect = app_module.get_db_connection
    state = {"calls": 0}

    def revoked_between_checks():
        state["calls"] += 1
        if state["calls"] == 2:
            with original_connect() as db:
                db.execute("UPDATE users SET role='student' WHERE id=3")
            state["expected"] = snapshot()
        return original_connect()

    monkeypatch.setattr(app_module, "get_db_connection", revoked_between_checks)
    response = admin_client.open(url, method=method, json=data)
    assert response.status_code == 403
    assert response.get_json()["error"]["message"] == AREA_DENIED
    assert snapshot() == state["expected"]


def test_failed_setting_write_preserves_existing_value(admin_client):
    assert admin_client.put("/api/admin/settings/support_contact", json={"value": "Original"}).status_code == 200
    before = snapshot()
    with closing(sqlite3.connect(app_module.DATABASE)) as db:
        db.execute("CREATE TRIGGER reject_setting BEFORE UPDATE ON system_settings "
                   "BEGIN SELECT RAISE(ABORT, 'private injected failure'); END")
    response = admin_client.put("/api/admin/settings/support_contact", json={"value": "Replacement"})
    assert response.status_code == 503
    assert "private injected failure" not in response.get_data(as_text=True)
    assert snapshot() == before
