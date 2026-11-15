"""US01 authentication coverage; case IDs are mapped in docs/testing.md."""

import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "test_auth.db"
    monkeypatch.setattr(app_module, "DATABASE", database)
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")
    with sqlite3.connect(database) as connection:
        connection.executescript((ROOT_DIR / "src/schema.sql").read_text())
        # Same public demo identities/password as init_db.py, seeded only here.
        password_hash = generate_password_hash("Password123!")
        connection.executemany(
            "INSERT INTO users (email, password_hash, full_name, role) "
            "VALUES (?, ?, ?, ?)",
            [
                ("student1@edusurvey.edu", password_hash, "Minh Nguyen", "student"),
                ("lecturer1@edusurvey.edu", password_hash, "Anh Nguyen", "lecturer"),
                ("admin@edusurvey.edu", password_hash, "Lan Tran", "administrator"),
            ],
        )
    with app_module.app.test_client() as test_client:
        yield test_client


def login(client, email="student1@edusurvey.edu", password="Password123!"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def assert_anonymous(client):
    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "role" not in session
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "email,role,user_id",
    [
        pytest.param("student1@edusurvey.edu", "student", 1, id="TC-01-student"),
        pytest.param("lecturer1@edusurvey.edu", "lecturer", 2, id="US01-A01-lecturer"),
        pytest.param("admin@edusurvey.edu", "administrator", 3, id="US01-A02-admin"),
    ],
)
def test_login_success(client, email, role, user_id):
    response = login(client, email)
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True
    assert data["user"]["id"] == user_id
    assert data["user"]["email"] == email
    assert data["user"]["role"] == role
    assert "password_hash" not in data["user"]
    with client.session_transaction() as session:
        assert dict(session) == {"user_id": user_id, "role": role}


def test_login_wrong_password(client):
    """TC-02: wrong password reveals no account-specific detail or session."""
    response = login(client, password="wrong-password")
    assert response.status_code == 401
    assert response.get_json()["error"] == {
        "code": "INVALID_CREDENTIALS",
        "message": "Email or password is incorrect.",
        "action": "Check your credentials and try again.",
    }
    assert_anonymous(client)


def test_login_unknown_email(client):
    """TC-03: unknown email has exactly the same error as a wrong password."""
    response = login(client, email="unknown@edusurvey.edu")
    known_response = login(client, password="wrong-password")
    assert response.status_code == known_response.status_code == 401
    assert response.get_json() == known_response.get_json()
    assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert_anonymous(client)


def test_login_missing_password(client):
    """TC-04: missing required credential is rejected without authenticating."""
    response = client.post("/api/auth/login", json={"email": "student1@edusurvey.edu"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_CREDENTIALS"
    assert response.get_json()["error"]["message"] == "Email and password are required."
    assert_anonymous(client)


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/auth/me", id="US01-A03-me"),
        pytest.param("/evaluations", id="US01-A04-list-page"),
        pytest.param("/evaluations/1/complete", id="US01-A05-complete-page"),
        pytest.param("/api/evaluations", id="US01-A06-list-api"),
    ],
)
def test_current_user_requires_login(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert response.get_json()["error"] == {
        "code": "UNAUTHORIZED",
        "message": "You must be logged in to access this resource.",
        "action": "Log in and try again.",
    }
    assert_anonymous(client)


def test_current_user_after_login(client):
    """US01-A07: session persists across requests, not across independent clients."""
    assert login(client).status_code == 200
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True
    assert data["user"] == {
        "id": 1, "email": "student1@edusurvey.edu", "full_name": "Minh Nguyen",
        "role": "student",
    }
    with app_module.app.test_client() as other_client:
        assert_anonymous(other_client)


@pytest.mark.parametrize(
    "email,expected_status",
    [
        pytest.param("student1@edusurvey.edu", 200, id="US01-A08-student"),
        pytest.param("lecturer1@edusurvey.edu", 403, id="US01-A09-lecturer"),
        pytest.param("admin@edusurvey.edu", 403, id="US01-A10-admin"),
    ],
)
def test_authenticated_student_access(client, email, expected_status):
    assert login(client, email).status_code == 200
    for path in ("/evaluations", "/evaluations/1/complete", "/api/evaluations"):
        response = client.get(path)
        assert response.status_code == expected_status
        if expected_status == 403:
            assert response.get_json()["error"]["code"] == "FORBIDDEN"
        elif path == "/api/evaluations":
            assert response.get_json() == {"count": 0, "evaluations": []}
        else:
            assert b"EduSurvey" in response.data


def test_login_replaces_previous_session(client):
    """US01-A11: changing account clears stale state and replaces the role."""
    assert login(client, "admin@edusurvey.edu").status_code == 200
    with client.session_transaction() as session:
        session["stale_state"] = "previous account"
    assert login(client).status_code == 200
    with client.session_transaction() as session:
        assert dict(session) == {"user_id": 1, "role": "student"}
    assert client.get("/evaluations").status_code == 200


def test_current_user_deleted_account(client):
    """US01-A12: a deleted account invalidates its authenticated session."""
    assert login(client).status_code == 200
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute("DELETE FROM users WHERE id = 1")
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.get_json()["error"]["message"] == "The authenticated user no longer exists."
    assert_anonymous(client)


def test_logout_clears_session(client):
    """TC-38 (US11): preserve the existing logout regression test."""
    assert login(client).status_code == 200
    with client.session_transaction() as session:
        assert "user_id" in session
        assert "role" in session
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}
    assert_anonymous(client)


def test_logout_success(client):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "student1@edusurvey.edu",
            "password": "Password123!",
        },
    )
    assert login_response.status_code == 200

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}


def test_protected_resource_after_logout_returns_401(client):
    client.post(
        "/api/auth/login",
        json={
            "email": "student1@edusurvey.edu",
            "password": "Password123!",
        },
    )

    client.post("/api/auth/logout")
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_logout_without_login(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}


def test_users_email_unique_constraint(client):
    database = app_module.DATABASE

    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO users (
                    email, password_hash, full_name, role
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "student1@edusurvey.edu",
                    "some-hash",
                    "Another Student",
                    "student",
                ),
            )
