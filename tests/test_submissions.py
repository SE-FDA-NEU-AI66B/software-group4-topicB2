
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "test_submissions.db"
    schema_path = ROOT_DIR / "src" / "schema.sql"

    with sqlite3.connect(database) as connection:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        connection.execute(
            """
            INSERT INTO users
                (email, password_hash, full_name, role)
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
            INSERT INTO course_enrollments (student_id, course_id)
            VALUES (1, 1)
            """
        )

        connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (1, 1, 'Test Evaluation', '2099-01-01 00:00:00', 'open')
            """
        )

        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (1, 'Rate the course', 'rating', 1, 1)
            """
        )

        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (1, 'Suggestions', 'text', 0, 2)
            """
        )

    monkeypatch.setattr(app_module, "DATABASE", database)
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    with app_module.app.test_client() as test_client:
        with test_client.session_transaction() as session:
            session["user_id"] = 1
        yield test_client


def test_submit_evaluation_success(client, tmp_path):
    response = client.post(
        "/api/submissions",
        json={
            "evaluation_id": 1,
            "answers": {
                "1": {"rating_value": 5},
                "2": {"text_value": "The course was useful."},
            },
        },
    )

    assert response.status_code == 201

    database = tmp_path / "test_submissions.db"
    with sqlite3.connect(database) as connection:
        saved_response = connection.execute(
            """
            SELECT id, status
            FROM responses
            WHERE evaluation_id = 1 AND student_id = 1
            """
        ).fetchone()

        saved_answers = connection.execute(
            """
            SELECT question_id, rating_value, text_value
            FROM response_answers
            WHERE response_id = ?
            ORDER BY question_id
            """,
            (saved_response[0],),
        ).fetchall()

    assert saved_response is not None
    assert saved_response[1] == "submitted"
    assert len(saved_answers) == 2
    assert saved_answers[0] == (1, 5, None)
    assert saved_answers[1] == (2, None, "The course was useful.")
