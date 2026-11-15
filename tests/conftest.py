"""Shared pytest fixtures for isolated application tests."""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a Flask test client backed by a temporary SQLite database."""
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

    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")

    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def fixed_app_clock(monkeypatch):
    """Freeze the application clock before seeding time-sensitive fixtures."""
    instant = datetime(2026, 11, 4, 12, 0, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant if tz is None else instant.replace(tzinfo=tz)

    monkeypatch.setattr(app_module, "datetime", FixedDateTime)
    return instant


@pytest.fixture
def api_client(tmp_path, monkeypatch, fixed_app_clock):
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
    monkeypatch.setitem(app_module.app.config, "TEST_DATABASE", str(database))
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")

    client = app_module.app.test_client()
    yield client
