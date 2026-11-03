import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "test_student_evaluations.db"
    monkeypatch.setattr(app_module, "DATABASE", database)

    now = datetime.now()

    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT,
                course_name TEXT NOT NULL
            );

            CREATE TABLE course_enrollments (
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL
            );

            CREATE TABLE course_lecturers (
                lecturer_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL
            );

            CREATE TABLE evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                created_by INTEGER,
                title TEXT NOT NULL,
                deadline TEXT,
                status TEXT NOT NULL
            );

            CREATE TABLE responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft'
            );
            """
        )

        connection.executemany(
            """
            INSERT INTO users
                (id, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "student@edusurvey.edu",
                    generate_password_hash("Password123!"),
                    "Student One",
                    "student",
                ),
                (
                    2,
                    "lecturer@edusurvey.edu",
                    generate_password_hash("Password123!"),
                    "Lecturer One",
                    "lecturer",
                ),
                (
                    3,
                    "otherstudent@edusurvey.edu",
                    generate_password_hash("Password123!"),
                    "Student Two",
                    "student",
                ),
            ],
        )

        connection.execute(
            """
            INSERT INTO courses (id, course_code, course_name)
            VALUES (1, 'SE101', 'Software Engineering')
            """
        )

        connection.execute(
            """
            INSERT INTO course_enrollments (student_id, course_id)
            VALUES (1, 1)
            """
        )

        connection.execute(
            """
            INSERT INTO course_lecturers (lecturer_id, course_id)
            VALUES (2, 1)
            """
        )

        connection.executemany(
            """
            INSERT INTO evaluations
                (id, course_id, created_by, title, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    1,
                    2,
                    "Course Feedback",
                    (now + timedelta(days=10)).isoformat(),
                    "open",
                ),
                (
                    2,
                    1,
                    2,
                    "Teaching Feedback",
                    (now + timedelta(days=2)).isoformat(),
                    "open",
                ),
                (
                    3,
                    1,
                    2,
                    "Previous Feedback",
                    (now - timedelta(days=2)).isoformat(),
                    "closed",
                ),
            ],
        )

    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )

    with app_module.app.test_client() as test_client:
        yield test_client


def login_as(client, user_id=1, role="student"):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = role


def test_student_evaluations_success(client):
    login_as(client)

    response = client.get("/api/evaluations")

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] == 3
    assert len(data["evaluations"]) == 3

    # Find the evaluation by title instead of assuming the first item.
    evaluation = next(
        item
        for item in data["evaluations"]
        if item["survey_title"] == "Course Feedback"
    )

    assert evaluation["course_name"] == "Software Engineering"
    assert evaluation["lecturer_name"] == "Lecturer One"
    assert evaluation["submission_deadline"] is not None
    assert evaluation["survey_status"] == "Active"

    assert set(evaluation.keys()) == {
        "survey_title",
        "course_name",
        "lecturer_name",
        "submission_deadline",
        "survey_status",
    }


def test_student_evaluations_due_soon(client):
    login_as(client)

    response = client.get("/api/evaluations")

    assert response.status_code == 200

    evaluations = response.get_json()["evaluations"]
    teaching = next(
        item
        for item in evaluations
        if item["survey_title"] == "Teaching Feedback"
    )

    assert teaching["survey_status"] == "Due soon"


def test_student_evaluations_closed(client):
    login_as(client)

    response = client.get("/api/evaluations")

    assert response.status_code == 200

    evaluations = response.get_json()["evaluations"]
    previous = next(
        item
        for item in evaluations
        if item["survey_title"] == "Previous Feedback"
    )

    assert previous["survey_status"] == "Closed"


def test_student_evaluations_completed(client):
    login_as(client)

    # Mark the first evaluation as submitted by this student.
    connection = app_module.get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO responses (evaluation_id, student_id, status)
            VALUES (?, ?, ?)
            """,
            (1, 1, "submitted"),
        )
        connection.commit()
    finally:
        connection.close()

    response = client.get("/api/evaluations")

    assert response.status_code == 200
    evaluations = response.get_json()["evaluations"]

    course_feedback = next(
        item
        for item in evaluations
        if item["survey_title"] == "Course Feedback"
    )

    assert course_feedback["survey_status"] == "Completed"


def test_student_evaluations_empty(client):
    # Student 3 is not enrolled in any course.
    login_as(client, user_id=3)

    response = client.get("/api/evaluations")

    assert response.status_code == 200
    assert response.get_json() == {
        "evaluations": [],
        "count": 0,
    }


def test_student_evaluations_requires_login(client):
    response = client.get("/api/evaluations")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_student_evaluations_forbidden_for_lecturer(client):
    login_as(client, user_id=2, role="lecturer")

    response = client.get("/api/evaluations")

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"


def test_student_only_sees_evaluations_for_enrolled_courses(client):
    login_as(client, user_id=3)

    response = client.get("/api/evaluations")

    assert response.status_code == 200
    assert response.get_json()["evaluations"] == []
