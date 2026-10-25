import sqlite3
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.app import app


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    # Create an isolated database for each test.
    database = tmp_path / "test_edusurvey.db"
    schema_path = ROOT_DIR / "src" / "schema.sql"

    with sqlite3.connect(database) as connection:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        # Student account used by submission tests.
        connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            ("student@test.com", "test-hash", "Test Student", "student"),
        )

        # Lecturer account used by evaluation-creation tests.
        connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "lecturer@test.com",
                "test-hash",
                "Test Lecturer",
                "lecturer",
            ),
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
            VALUES (?, ?)
            """,
            (1, 1),
        )

        # Assign lecturer id 2 to course id 1.
        connection.execute(
            """
            INSERT INTO course_lecturers (lecturer_id, course_id)
            VALUES (2, 1)
            """
        )

        connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (1, 1, 'Test Evaluation', ?, 'open')
            """,
            ("2099-01-01 00:00:00",),
        )

        # Add a rating question.
        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (1, 'Rate the course', 'rating', 1, 1)
            """
        )

        # Add a text question for written feedback.
        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (1, 'What did you think of the course content?',
                    'text', 0, 2)
            """
        )

        # Add a submitted response for the feedback API.
        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, submitted_at, status)
            VALUES (1, 1, CURRENT_TIMESTAMP, 'submitted')
            """
        )

        response_id = connection.execute(
            """
            SELECT id FROM responses
            WHERE evaluation_id = 1 AND student_id = 1
            """
        ).fetchone()[0]

        text_question_id = connection.execute(
            """
            SELECT id FROM questions
            WHERE evaluation_id = 1 AND question_type = 'text'
            """
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, text_value)
            VALUES (?, ?, ?)
            """,
            (
                response_id,
                text_question_id,
                "The course content was very useful.",
            ),
        )
        connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "admin@test.com",
                "test-hash",
                "Test Administrator",
                "administrator",
            ),
        )

    # Redirect the application to the temporary database.
    monkeypatch.setattr("src.app.DATABASE", database)
    app.config["TEST_DATABASE"] = str(database)
    app.config.update(TESTING=True)

    client = app.test_client()
    yield client

    app.config.update(TESTING=False)