import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module


@pytest.fixture
def submission_client(tmp_path, monkeypatch):
    """Create a clean database for each submission test."""

    database = tmp_path / "test_submission.db"
    schema_path = ROOT_DIR / "src" / "schema.sql"

    with sqlite3.connect(database) as connection:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        # Create student and lecturer.
        connection.executemany(
            """
            INSERT INTO users
                (id, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "student@test.com",
                    "test-hash",
                    "Test Student",
                    "student",
                ),
                (
                    2,
                    "lecturer@test.com",
                    "test-hash",
                    "Test Lecturer",
                    "lecturer",
                ),
            ],
        )

        # Create course.
        connection.execute(
            """
            INSERT INTO courses
                (id, course_code, course_name)
            VALUES (1, 'TEST101', 'Test Course')
            """
        )

        # Enroll student.
        connection.execute(
            """
            INSERT INTO course_enrollments
                (student_id, course_id)
            VALUES (1, 1)
            """
        )

        # Create an open evaluation.
        connection.execute(
            """
            INSERT INTO evaluations
                (id, course_id, created_by, title, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                1,
                2,
                "Test Evaluation",
                "2099-01-01T00:00:00",
                "open",
            ),
        )

        # Required rating question.
        connection.execute(
            """
            INSERT INTO questions
                (id, evaluation_id, question_text,
                 question_type, is_required, question_order)
            VALUES (1, 1, 'Rate the course', 'rating', 1, 1)
            """
        )

        # Required text question.
        connection.execute(
            """
            INSERT INTO questions
                (id, evaluation_id, question_text,
                 question_type, is_required, question_order)
            VALUES (2, 1, 'Give your feedback', 'text', 1, 2)
            """
        )

    monkeypatch.setattr(app_module, "DATABASE", database)

    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        TEST_DATABASE=str(database),
    )

    with app_module.app.test_client() as client:
        yield client


def login_student(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "student"


def valid_submission_payload():
    return {
        "evaluation_id": 1,
        "answers": {
            "1": {"rating_value": 5},
            "2": {"text_value": "The course is useful."},
        },
    }


def get_database_counts(client):
    database = client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        response_count = connection.execute(
            "SELECT COUNT(*) FROM responses"
        ).fetchone()[0]

        answer_count = connection.execute(
            "SELECT COUNT(*) FROM response_answers"
        ).fetchone()[0]

    return response_count, answer_count


def test_submission_success_persists_response_and_answers(
    submission_client,
):
    login_student(submission_client)

    response = submission_client.post(
        "/api/submissions",
        json=valid_submission_payload(),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["status"] == "submitted"
    assert data["evaluation_id"] == 1
    assert data["response_id"] is not None

    database = submission_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        submitted = connection.execute(
            """
            SELECT status, submitted_at
            FROM responses
            WHERE evaluation_id = 1 AND student_id = 1
            """
        ).fetchone()

        answers = connection.execute(
            """
            SELECT question_id, rating_value, text_value
            FROM response_answers
            WHERE response_id = ?
            ORDER BY question_id
            """,
            (data["response_id"],),
        ).fetchall()

    assert submitted is not None
    assert submitted[0] == "submitted"
    assert submitted[1] is not None

    assert len(answers) == 2
    assert answers[0] == (1, 5, None)
    assert answers[1] == (2, None, "The course is useful.")

def test_submission_missing_required_answer_does_not_create_records(
    submission_client,
):
    login_student(submission_client)

    response = submission_client.post(
        "/api/submissions",
        json={
            "evaluation_id": 1,
            "answers": {
                "1": {"rating_value": 5}
            },
        },
    )

    assert response.status_code == 400
    assert (
        response.get_json()["error"]["code"]
        == "MISSING_REQUIRED_ANSWERS"
    )

    response_count, answer_count = get_database_counts(
        submission_client
    )

    assert response_count == 0
    assert answer_count == 0

def test_duplicate_submission_does_not_modify_existing_records(
    submission_client,
):
    login_student(submission_client)

    database = submission_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, status)
            VALUES (1, 1, 'submitted')
            """
        )

        response_id = connection.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, rating_value)
            VALUES (?, 1, 4)
            """,
            (response_id,),
        )

    response = submission_client.post(
        "/api/submissions",
        json=valid_submission_payload(),
    )

    assert response.status_code == 409

    assert (
        response.get_json()["error"]["code"]
        == "DUPLICATE_SUBMISSION"
    )

    response_count, answer_count = get_database_counts(
        submission_client
    )

    assert response_count == 1
    assert answer_count == 1

    with sqlite3.connect(database) as connection:
        original_rating = connection.execute(
            """
            SELECT rating_value
            FROM response_answers
            WHERE response_id = ? AND question_id = 1
            """,
            (response_id,),
        ).fetchone()[0]

    assert original_rating == 4

def test_submission_after_deadline_does_not_create_records(
    submission_client,
):
    login_student(submission_client)

    database = submission_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            UPDATE evaluations
            SET deadline = ?
            WHERE id = 1
            """,
            ("2000-01-01T00:00:00",),
        )

    response = submission_client.post(
        "/api/submissions",
        json=valid_submission_payload(),
    )

    assert response.status_code == 400

    assert (
        response.get_json()["error"]["code"]
        == "DEADLINE_EXPIRED"
    )

    response_count, answer_count = get_database_counts(
        submission_client
    )

    assert response_count == 0
    assert answer_count == 0

def test_submission_invalid_evaluation_does_not_create_records(
    submission_client,
):
    login_student(submission_client)

    payload = valid_submission_payload()
    payload["evaluation_id"] = 9999

    response = submission_client.post(
        "/api/submissions",
        json=payload,
    )

    assert response.status_code == 404

    assert (
        response.get_json()["error"]["code"]
        == "EVALUATION_NOT_FOUND"
    )

    response_count, answer_count = get_database_counts(
        submission_client
    )

    assert response_count == 0
    assert answer_count == 0

def test_submission_closed_evaluation_does_not_create_records(
    submission_client,
):
    login_student(submission_client)

    database = submission_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            UPDATE evaluations
            SET status = 'closed'
            WHERE id = 1
            """
        )

    response = submission_client.post(
        "/api/submissions",
        json=valid_submission_payload(),
    )

    assert response.status_code == 400

    assert (
        response.get_json()["error"]["code"]
        == "EVALUATION_CLOSED"
    )

    response_count, answer_count = get_database_counts(
        submission_client
    )

    assert response_count == 0
    assert answer_count == 0


@pytest.mark.parametrize(
    "deadline_offset, expected_status, expected_code",
    [
        (timedelta(microseconds=-1), 400, "DEADLINE_EXPIRED"),
        (timedelta(0), 201, None),
        (timedelta(microseconds=1), 201, None),
    ],
)
def test_submission_deadline_boundary(
    submission_client,
    monkeypatch,
    deadline_offset,
    expected_status,
    expected_code,
):
    login_student(submission_client)

    fixed_now = datetime(2026, 11, 4, 12, 0, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now
            return fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(
        app_module,
        "datetime",
        FixedDateTime,
    )

    deadline = fixed_now + deadline_offset

    database = submission_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            UPDATE evaluations
            SET deadline = ?
            WHERE id = 1
            """,
            (deadline.isoformat(),),
        )

    response = submission_client.post(
        "/api/submissions",
        json=valid_submission_payload(),
    )

    assert response.status_code == expected_status

    if expected_code:
        assert response.get_json()["error"]["code"] == expected_code
        response_count, answer_count = get_database_counts(
            submission_client
        )
        assert response_count == 0
        assert answer_count == 0
    else:
        assert response.get_json()["status"] == "submitted"
        response_count, answer_count = get_database_counts(
            submission_client
        )
        assert response_count == 1
        assert answer_count == 2
