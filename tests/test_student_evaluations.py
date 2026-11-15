"""US02 API tests with isolated SQLite data and a frozen clock.

Case IDs in docstrings and parameter IDs map to docs/testing.md.
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module

NOW = datetime(2026, 11, 3, 12, 0, 0)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz is None else NOW.replace(tzinfo=tz)


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "test_student_evaluations.db"
    monkeypatch.setattr(app_module, "DATABASE", database)
    monkeypatch.setattr(app_module, "datetime", FixedDateTime)
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")

    with sqlite3.connect(database) as connection:
        connection.executescript((ROOT_DIR / "src/schema.sql").read_text())
        connection.executemany(
            "INSERT INTO users (id, email, password_hash, full_name, role, created_at) "
            "VALUES (?, ?, 'unused-session-fixture', ?, ?, ?)",
            [
                (1, "student@test.edu", "Student One", "student", NOW.isoformat()),
                (2, "lecturer@test.edu", "Lecturer One", "lecturer", NOW.isoformat()),
                (3, "otherstudent@test.edu", "Student Two", "student", NOW.isoformat()),
                (4, "admin@test.edu", "Administrator", "administrator", NOW.isoformat()),
            ],
        )
        connection.execute(
            "INSERT INTO courses (id, course_code, course_name, created_at) "
            "VALUES (1, 'SE101', 'Software Engineering', ?)", (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO course_enrollments (student_id, course_id, enrolled_at) "
            "VALUES (1, 1, ?)", (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO course_lecturers (lecturer_id, course_id, assigned_at) "
            "VALUES (2, 1, ?)", (NOW.isoformat(),),
        )
        connection.executemany(
            "INSERT INTO evaluations "
            "(id, course_id, created_by, title, deadline, status, created_at) "
            "VALUES (?, 1, 2, ?, ?, ?, ?)",
            [
                (1, "Course Feedback", (NOW + timedelta(days=10)).isoformat(), "open", NOW.isoformat()),
                (2, "Teaching Feedback", (NOW + timedelta(hours=12)).isoformat(), "open", NOW.isoformat()),
                (3, "Previous Feedback", (NOW - timedelta(days=2)).isoformat(), "closed", NOW.isoformat()),
            ],
        )
    with app_module.app.test_client() as test_client:
        yield test_client


def login_as(client, user_id=1, role="student"):
    # US02 isolates list authorization; actual credential login is covered by US01.
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = role


def evaluation_list(client, query_string=None):
    response = client.get("/api/evaluations", query_string=query_string)
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == len(data["evaluations"])
    return data["evaluations"]


def evaluation(client, evaluation_id):
    return next(item for item in evaluation_list(client) if item["id"] == evaluation_id)


def test_student_evaluations_success(client):
    """TC-05: all five display details and exact IDs/count are returned."""
    login_as(client)
    items = evaluation_list(client)
    assert {item["id"] for item in items} == {1, 2, 3}
    assert len(items) == 3
    assert next(item for item in items if item["id"] == 1) == {
        "id": 1,
        "survey_title": "Course Feedback",
        "course_name": "Software Engineering",
        "lecturer_name": "Lecturer One",
        "submission_deadline": (NOW + timedelta(days=10)).isoformat(),
        "survey_status": "Active",
    }


def test_student_evaluations_three_active(client):
    """US02-L12: return exactly three active evaluations for the current student."""
    expected = {
        evaluation_id: {
            "id": evaluation_id,
            "survey_title": f"Active Evaluation {evaluation_id}",
            "course_name": "Software Engineering",
            "lecturer_name": "Lecturer One",
            "submission_deadline": (NOW + timedelta(days=evaluation_id + 1)).isoformat(),
            "survey_status": "Active",
        }
        for evaluation_id in (1, 2, 3)
    }
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.executemany(
            "UPDATE evaluations SET title = ?, deadline = ?, status = 'open' WHERE id = ?",
            [
                (item["survey_title"], item["submission_deadline"], evaluation_id)
                for evaluation_id, item in expected.items()
            ],
        )
        connection.execute(
            "INSERT INTO courses (id, course_code, course_name, created_at) "
            "VALUES (2, 'OTHER101', 'Other Student Course', ?)",
            (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO course_enrollments (student_id, course_id, enrolled_at) "
            "VALUES (3, 2, ?)",
            (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO course_lecturers (lecturer_id, course_id, assigned_at) "
            "VALUES (2, 2, ?)",
            (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO evaluations "
            "(id, course_id, created_by, title, deadline, status, created_at) "
            "VALUES (4, 2, 2, 'Other Student Evaluation', ?, 'open', ?)",
            ((NOW + timedelta(days=5)).isoformat(), NOW.isoformat()),
        )
        assert connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0

    login_as(client)
    response = client.get("/api/evaluations")

    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 3
    assert len(data["evaluations"]) == 3
    assert {item["id"]: item for item in data["evaluations"]} == expected


def test_student_evaluations_due_soon(client):
    """US02-L01: an unfinished open evaluation with 12h left is Due soon."""
    login_as(client)
    assert evaluation(client, 2)["survey_status"] == "Due soon"


def test_student_evaluations_closed(client):
    """US02-L02: an explicitly closed evaluation remains Closed before deadline."""
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "UPDATE evaluations SET deadline = ? WHERE id = 3",
            ((NOW + timedelta(days=10)).isoformat(),),
        )
    login_as(client)
    assert evaluation(client, 3)["survey_status"] == "Closed"


@pytest.mark.parametrize(
    "status,offset",
    [
        pytest.param("open", 10, id="US02-L03-open"),
        pytest.param("open", -2, id="US02-L04-expired"),
        pytest.param("closed", -2, id="US02-L05-closed"),
    ],
)
def test_student_evaluations_completed(client, status, offset):
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "UPDATE evaluations SET status = ?, deadline = ? WHERE id = 1",
            (status, (NOW + timedelta(days=offset)).isoformat()),
        )
        connection.execute(
            "INSERT INTO responses (evaluation_id, student_id, status, submitted_at) "
            "VALUES (1, 1, 'submitted', ?)", (NOW.isoformat(),),
        )
    login_as(client)
    assert evaluation(client, 1)["survey_status"] == "Completed"


def test_student_evaluations_empty(client):
    """US02-L06: a student with no enrollments receives the exact empty state."""
    login_as(client, user_id=3)
    response = client.get("/api/evaluations")
    assert response.status_code == 200
    assert response.get_json() == {"evaluations": [], "count": 0}


def test_student_evaluations_requires_login(client):
    """TC-06: anonymous access returns 401 without evaluation data."""
    response = client.get("/api/evaluations")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"
    assert "evaluations" not in response.get_json()


@pytest.mark.parametrize(
    "user_id,role",
    [
        pytest.param(2, "lecturer", id="TC-07-lecturer"),
        pytest.param(4, "administrator", id="US02-L07-administrator"),
    ],
)
def test_student_evaluations_forbidden_for_lecturer(client, user_id, role):
    login_as(client, user_id=user_id, role=role)
    response = client.get("/api/evaluations")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"
    assert "evaluations" not in response.get_json()


def test_student_only_sees_evaluations_for_enrolled_courses(client):
    """US02-L08: two students with disjoint enrollments cannot impersonate via query."""
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "INSERT INTO courses (id, course_code, course_name, created_at) "
            "VALUES (2, 'PRIVATE', 'Student Two Course', ?)", (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO course_enrollments (student_id, course_id, enrolled_at) "
            "VALUES (3, 2, ?)", (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO evaluations "
            "(id, course_id, created_by, title, deadline, status, created_at) "
            "VALUES (4, 2, 2, 'Private Evaluation', ?, 'open', ?)",
            ((NOW + timedelta(days=2)).isoformat(), NOW.isoformat()),
        )
    login_as(client)
    assert {item["id"] for item in evaluation_list(client, {"student_id": 3, "user_id": 3})} == {1, 2, 3}
    login_as(client, user_id=3)
    items = evaluation_list(client, {"student_id": 1, "user_id": 1})
    assert [item["id"] for item in items] == [4]
    assert items[0]["course_name"] == "Student Two Course"


@pytest.mark.parametrize(
    "seconds,expected",
    [
        pytest.param(86399, "Due soon", id="TC-08-below"),
        pytest.param(86400, "Active", id="TC-09-at"),
        pytest.param(86401, "Active", id="TC-10-above"),
    ],
)
def test_student_evaluations_due_soon_24_hour_boundary(client, seconds, expected):
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "UPDATE evaluations SET deadline = ? WHERE id = 1",
            ((NOW + timedelta(seconds=seconds)).isoformat(),),
        )
    login_as(client)
    assert evaluation(client, 1)["survey_status"] == expected


@pytest.mark.parametrize(
    "seconds,expected",
    [
        pytest.param(-1, "Closed", id="TC-11-before"),
        pytest.param(0, "Closed", id="TC-12-at"),
        pytest.param(1, "Due soon", id="TC-13-after"),
    ],
)
def test_student_evaluations_deadline_boundary(client, seconds, expected):
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "UPDATE evaluations SET deadline = ? WHERE id = 1",
            ((NOW + timedelta(seconds=seconds)).isoformat(),),
        )
    login_as(client)
    assert evaluation(client, 1)["survey_status"] == expected


def test_student_completion_is_personal(client):
    """US02-L09: another enrolled student's submission cannot mark mine Completed."""
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "INSERT INTO course_enrollments (student_id, course_id, enrolled_at) "
            "VALUES (3, 1, ?)", (NOW.isoformat(),),
        )
        connection.execute(
            "INSERT INTO responses (evaluation_id, student_id, status, submitted_at) "
            "VALUES (1, 3, 'submitted', ?)", (NOW.isoformat(),),
        )
    login_as(client)
    assert evaluation(client, 1)["survey_status"] == "Active"
    login_as(client, user_id=3)
    assert evaluation(client, 1)["survey_status"] == "Completed"


def test_draft_response_is_not_completed(client):
    """US02-L10: a draft response is unfinished, so its evaluation remains Active."""
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute(
            "INSERT INTO responses (evaluation_id, student_id, status) VALUES (1, 1, 'draft')"
        )
    login_as(client)
    assert evaluation(client, 1)["survey_status"] == "Active"


def test_draft_evaluation_is_hidden(client):
    """US02-L11: unpublished evaluations are not in the student's list."""
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute("UPDATE evaluations SET status = 'draft' WHERE id = 1")
    login_as(client)
    assert {item["id"] for item in evaluation_list(client)} == {2, 3}
