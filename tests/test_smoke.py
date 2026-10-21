
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.app import app


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    # Use a separate temporary database for API tests.
    database = tmp_path / "test_edusurvey.db"
    schema_path = ROOT_DIR / "src" / "schema.sql"

    with sqlite3.connect(database) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))

        connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            ("student@test.com", "test-hash", "Test Student", "student"),
        )

        connection.execute(
            """
            INSERT INTO courses (course_code, course_name)
            VALUES (?, ?)
            """,
            ("TEST101", "Test Course"),
        )

        connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (1, 1, 'Test Evaluation', ?, 'open')
            """,
            ("2099-01-01 00:00:00",),
        )

        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (1, 'Rate the course', 'rating', 1, 1)
            """
        )

    # Redirect the application to the temporary database.
    monkeypatch.setattr("src.app.DATABASE", database)
    app.config["TEST_DATABASE"] = str(database)

    app.config.update(TESTING=True)
    client = app.test_client()

    yield client

    # Restore testing configuration.
    app.config.update(TESTING=False)


def login_as_student(client):
    with client.session_transaction() as session:
        session["user_id"] = 1


def valid_payload():
    return {
        "user_id": 1,
        "evaluation_id": 1,
        "answers": {
            "1": {"rating_value": 5}
        },
    }

def test_home_route():
    response = app.test_client().get("/")
    assert response.status_code == 200


def test_evaluations_route():
    response = app.test_client().get("/evaluations")

    assert response.status_code == 200
    assert b"EduSurvey" in response.data


def test_submission_requires_login(api_client):
    response = api_client.post(
        "/api/submissions",
        json={
            "evaluation_id": 1,
            "answers": {"1": {"rating_value": 5}},
        },
    )

    assert response.status_code == 401
    assert response.json["error"]["code"] == "UNAUTHORIZED"



def test_submission_missing_required_answers(api_client):
    login_as_student(api_client)

    response = api_client.post(
        "/api/submissions",
        json={
            "evaluation_id": 1,
            "answers": {},
        },
    )

    assert response.status_code == 400
    assert (
        response.json["error"]["code"]
        == "MISSING_REQUIRED_ANSWERS"
    )



def test_submission_expired_deadline(api_client):
    login_as_student(api_client)
        

    # The test database path is configured by the fixture below.
    database = api_client.application.config["TEST_DATABASE"]
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE evaluations SET deadline = ? WHERE id = 1",
            ("2000-01-01 00:00:00",),
        )

    response = api_client.post(
        "/api/submissions",
        json=valid_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "DEADLINE_EXPIRED"



def test_duplicate_submission(api_client):
    login_as_student(api_client)

    database = api_client.application.config["TEST_DATABASE"]
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, submitted_at, status)
            VALUES (1, 1, CURRENT_TIMESTAMP, 'submitted')
            """
        )

    response = api_client.post(
        "/api/submissions",
        json=valid_payload(),
    )

    assert response.status_code == 409
    assert (
        response.json["error"]["code"]
        == "DUPLICATE_SUBMISSION"
    )


    assert response.status_code == 409
    assert response.json["error"]["code"] == "DUPLICATE_SUBMISSION"


def test_submission_invalid_evaluation(api_client):
    login_as_student(api_client)

    response = api_client.post(
        "/api/submissions",
        json={
            "evaluation_id": 9999,
            "answers": {"1": {"rating_value": 5}},
        },
    )

    assert response.status_code == 404
    assert response.json["error"]["code"] == "EVALUATION_NOT_FOUND"


def test_submission_closed_evaluation(api_client):
    login_as_student(api_client)

    database = api_client.application.config["TEST_DATABASE"]
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE evaluations SET status = 'closed' WHERE id = 1"
        )

    response = api_client.post(
        "/api/submissions",
        json=valid_payload(),
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "EVALUATION_CLOSED"


def test_submission_errors_have_user_facing_guidance(api_client):
    response = api_client.post(
        "/api/submissions",
        json=valid_payload(),
    )

    assert response.status_code == 401
    error = response.json["error"]

    assert error["code"] == "UNAUTHORIZED"
    assert error["message"]
    assert error["action"]
