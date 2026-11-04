
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
    database = tmp_path / "test_edusurvey.db"
    monkeypatch.setattr(app_module, "DATABASE", database)

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "student1@edusurvey.edu",
                generate_password_hash("Password123!"),
                "Minh Nguyen",
                "student",
            ),
        )

    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )

    with app_module.app.test_client() as test_client:
        yield test_client


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "student1@edusurvey.edu",
            "password": "Password123!",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True
    assert data["user"]["role"] == "student"
    assert "password_hash" not in data["user"]


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "student1@edusurvey.edu",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@edusurvey.edu",
            "password": "Password123!",
        },
    )

    assert response.status_code == 401


def test_login_missing_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "student1@edusurvey.edu"},
    )

    assert response.status_code == 400


def test_current_user_requires_login(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_current_user_after_login(client):
    client.post(
        "/api/auth/login",
        json={
            "email": "student1@edusurvey.edu",
            "password": "Password123!",
        },
    )

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "student1@edusurvey.edu"


def test_logout_clears_session(client):
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


def test_logout_clears_session(client):
    client.post(
        "/api/auth/login",
        json={
            "email": "student1@edusurvey.edu",
            "password": "Password123!",
        },
    )

    with client.session_transaction() as session:
        assert "user_id" in session
        assert "role" in session

    client.post("/api/auth/logout")

    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "role" not in session


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
