"""US01 authentication coverage; case IDs are mapped in docs/testing.md."""

import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module

# Public demo values from init_db.py, used only in the isolated test database.
DEMO_CREDENTIALS = {
    "password": "Password123!",
    "invalid_password": "wrong-password",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "test_auth.db"
    monkeypatch.setattr(app_module, "DATABASE", database)
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")
    with sqlite3.connect(database) as connection:
        connection.executescript((ROOT_DIR / "src/schema.sql").read_text())
        # Same public demo identities/password as init_db.py, seeded only here.
        password_hash = generate_password_hash(DEMO_CREDENTIALS["password"])
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


def login(client, email="student1@edusurvey.edu", password=None):
    if password is None:
        password = DEMO_CREDENTIALS["password"]
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
    response = login(client, password=DEMO_CREDENTIALS["invalid_password"])
    assert response.status_code == 401
    assert response.get_json()["error"] == {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password.",
        "action": "Check your credentials and try again.",
    }
    assert_anonymous(client)


def test_login_unknown_email(client):
    """TC-03: unknown email has exactly the same error as a wrong password."""
    response = login(client, email="unknown@edusurvey.edu")
    known_response = login(client, password=DEMO_CREDENTIALS["invalid_password"])
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
    if not path.startswith("/api/"):
        assert response.status_code == 302
        assert response.headers["Location"] == "/login"
        assert client.get(response.headers["Location"]).status_code == 200
        assert_anonymous(client)
        return
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

    with sqlite3.connect(database) as connection, pytest.raises(sqlite3.IntegrityError):
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


@pytest.fixture
def logout_client(client, fixed_app_clock):
    """Seed real protected data for TC-39/40 in the existing temporary auth DB."""
    from contextlib import closing

    timestamp = fixed_app_clock.strftime("%Y-%m-%d %H:%M:%S")
    with closing(sqlite3.connect(app_module.DATABASE)) as connection, connection:
        connection.execute(
            "INSERT INTO courses (id, course_code, course_name, created_at) "
            "VALUES (1, 'LOGOUT101', 'PRIVATE_STUDENT_COURSE', ?)", (timestamp,),
        )
        connection.execute(
            "INSERT INTO course_enrollments (student_id, course_id, enrolled_at) "
            "VALUES (1, 1, ?)", (timestamp,),
        )
        connection.execute(
            "INSERT INTO course_lecturers (lecturer_id, course_id, assigned_at) "
            "VALUES (2, 1, ?)", (timestamp,),
        )
        connection.execute(
            "INSERT INTO evaluations (id, course_id, created_by, title, deadline, status, created_at) "
            "VALUES (1, 1, 2, 'PRIVATE_EVALUATION', '2026-11-10 12:00:00', 'open', ?)",
            (timestamp,),
        )
        connection.execute(
            "INSERT INTO questions (id, evaluation_id, question_text, question_type, is_required, question_order) "
            "VALUES (1, 1, 'Course feedback', 'text', 1, 1)"
        )
        connection.execute(
            "INSERT INTO responses (id, evaluation_id, student_id, submitted_at, status) "
            "VALUES (1, 1, 1, ?, 'submitted')", (timestamp,),
        )
        connection.execute(
            "INSERT INTO response_answers (response_id, question_id, text_value) "
            "VALUES (1, 1, 'PRIVATE_SUBMITTED_FEEDBACK')"
        )
    return client


def test_student_page_denied_after_logout(logout_client):
    """TC-39 / US11 #183 + US02 #18: a real student loses page/API access."""
    client = logout_client
    authenticated = login(client)
    assert authenticated.status_code == 200
    assert authenticated.get_json()["user"]["role"] == "student"
    assert client.get("/evaluations").status_code == 200
    before = client.get("/api/evaluations")
    assert before.status_code == 200
    assert before.get_json()["count"] == 1
    assert b"PRIVATE_STUDENT_COURSE" in before.data

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.get_json() == {"authenticated": False}
    assert_anonymous(client)
    for path in ("/evaluations", "/api/evaluations"):
        response = client.get(path, follow_redirects=False)
        if path == "/evaluations":
            assert response.status_code == 302
            assert response.headers["Location"] == "/login"
            assert b"PRIVATE_STUDENT_COURSE" not in response.data
            continue
        assert response.status_code == 401
        assert response.is_json
        assert response.get_json() == {"error": {
            "code": "UNAUTHORIZED",
            "message": "You must be logged in to access this resource.",
            "action": "Log in and try again.",
        }}
        assert "Location" not in response.headers
        assert b"PRIVATE_STUDENT_COURSE" not in response.data
        assert b"PRIVATE_EVALUATION" not in response.data


def test_lecturer_feedback_denied_after_logout(logout_client):
    """TC-40 / US11 #183 + US04 #50: an assigned lecturer loses real feedback."""
    client = logout_client
    authenticated = login(client, "lecturer1@edusurvey.edu")
    assert authenticated.status_code == 200
    assert authenticated.get_json()["user"]["role"] == "lecturer"
    before = client.get("/api/courses/1/feedback")
    assert before.status_code == 200
    assert before.get_json()["completed_evaluations"] == 1
    assert b"PRIVATE_SUBMITTED_FEEDBACK" in before.data

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.get_json() == {"authenticated": False}
    assert_anonymous(client)
    response = client.get("/api/courses/1/feedback", follow_redirects=False)
    assert response.status_code == 401
    assert response.is_json
    assert response.get_json() == {"error": {
        "code": "UNAUTHORIZED",
        "message": "You must be logged in to access this resource.",
        "action": "Log in and try again.",
    }}
    assert "Location" not in response.headers
    assert b"PRIVATE_SUBMITTED_FEEDBACK" not in response.data
    assert b"PRIVATE_STUDENT_COURSE" not in response.data


def test_anonymous_logout_is_idempotent(client, fixed_app_clock):
    """TC-41 / US11 #183: two anonymous logouts succeed and remain anonymous."""
    assert_anonymous(client)
    for _ in range(2):
        response = client.post("/api/auth/logout", follow_redirects=False)
        assert response.status_code == 200
        assert response.is_json
        assert response.get_json() == {"authenticated": False}
        assert "Location" not in response.headers
        assert_anonymous(client)


@pytest.mark.parametrize("email,paths", [
    ("student1@edusurvey.edu", ["/evaluations", "/evaluations/1/complete", "/account"]),
    ("lecturer1@edusurvey.edu", ["/lecturer/feedback", "/lecturer/feedback/1", "/account"]),
    ("admin@edusurvey.edu", ["/account"]),
])
def test_protected_html_redirects_after_logout(logout_client, email, paths):
    """P0C-08 / #215: HTML navigates to login while APIs retain JSON 401."""
    client = logout_client
    assert login(client, email).status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert_anonymous(client)
    for path in paths:
        response = client.get(path, headers={"Accept": "text/html"}, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"] == "/login"
        assert client.get(response.headers["Location"]).status_code == 200
    assert client.get("/api/evaluations").status_code == 401


@pytest.mark.parametrize("email,path,accept,expected", [
    ("student1@edusurvey.edu", "/evaluations", "text/html", 302),
    ("student1@edusurvey.edu", "/evaluations/1/complete", "text/html", 302),
    ("student1@edusurvey.edu", "/api/evaluations", "application/json", 401),
    ("lecturer1@edusurvey.edu", "/lecturer/feedback", "text/html", 302),
    ("lecturer1@edusurvey.edu", "/api/courses/1/feedback", "application/json", 401),
    ("admin@edusurvey.edu", "/account", "text/html", 302),
])
def test_deleted_account_cannot_reuse_protected_session(client, email, path, accept, expected):
    """EX-A01: deletion invalidates direct access without first visiting /auth/me."""
    assert login(client, email).status_code == 200
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("DELETE FROM users WHERE email=?", (email,))
    result = client.get(path, headers={"Accept": accept})
    assert result.status_code == expected
    if expected == 302:
        assert result.headers["Location"] == "/login"
    else:
        assert result.get_json()["error"]["code"] == "UNAUTHORIZED"
    assert_anonymous(client)


def test_expired_signed_session_cannot_access_protected_data(client, monkeypatch):
    """EX-S02: a genuinely over-age signed cookie is rejected, not just removed."""
    from itsdangerous import TimestampSigner

    clock = {"timestamp": 1_700_000_000}
    monkeypatch.setattr(TimestampSigner, 'get_timestamp', lambda self: clock['timestamp'])
    assert login(client).status_code == 200
    assert client.get('/api/auth/me').status_code == 200
    clock['timestamp'] += int(app_module.app.permanent_session_lifetime.total_seconds()) + 1
    assert client.get('/api/auth/me').status_code == 401
    result = client.get('/api/evaluations')
    assert result.status_code == 401
    assert set(result.get_json()) == {'error'}
    assert_anonymous(client)
