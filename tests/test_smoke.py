
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

    # Redirect the application to the temporary database.
    monkeypatch.setattr("src.app.DATABASE", database)
    app.config["TEST_DATABASE"] = str(database)
    app.config.update(TESTING=True)

    client = app.test_client()
    yield client

    app.config.update(TESTING=False)


def login_as_student(client):
    with client.session_transaction() as session:
        session["user_id"] = 1


def valid_payload():
    return {
        "user_id": 1,
        "evaluation_id": 1,
        "answers": {
            "1": {"rating_value": 5},
        },
    }


def add_feedback(database, comment, student_id):
    """Add one submitted text response to evaluation 1."""
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, submitted_at, status)
            VALUES (1, ?, CURRENT_TIMESTAMP, 'submitted')
            """,
            (student_id,),
        )

        response_id = connection.execute(
            """
            SELECT id FROM responses
            WHERE evaluation_id = 1 AND student_id = ?
            """,
            (student_id,),
        ).fetchone()[0]

        question_id = connection.execute(
            """
            SELECT id FROM questions
            WHERE evaluation_id = 1 AND question_type = 'text'
            """,
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, text_value)
            VALUES (?, ?, ?)
            """,
            (response_id, question_id, comment),
        )


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
    assert response.json["error"]["code"] == "MISSING_REQUIRED_ANSWERS"


def test_submission_expired_deadline(api_client):
    login_as_student(api_client)

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

    response = api_client.post(
        "/api/submissions",
        json=valid_payload(),
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


def test_grouped_feedback_response_structure(api_client):
    response = api_client.get("/api/evaluations/1/feedback/topics")

    assert response.status_code == 200
    data = response.get_json()

    assert data["evaluation_id"] == 1
    assert "topics" in data

    topics = data["topics"]
    topic_names = {topic["topic"] for topic in topics}

    assert {
        "Course Content",
        "Teaching Delivery",
        "Workload",
        "Assessment",
        "Other",
    }.issubset(topic_names)

    for topic in topics:
        assert isinstance(topic["count"], int)
        assert topic["count"] == len(topic["comments"])


def test_grouped_feedback_excludes_other_evaluations(api_client):
    database = api_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (1, 1, 'Another Evaluation', '2099-01-01 00:00:00', 'open')
            """
        )

        other_evaluation_id = connection.execute(
            "SELECT id FROM evaluations WHERE title = ?",
            ("Another Evaluation",),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (?, 'Other feedback', 'text', 0, 1)
            """,
            (other_evaluation_id,),
        )

        other_question_id = connection.execute(
            """
            SELECT id FROM questions
            WHERE evaluation_id = ? AND question_type = 'text'
            """,
            (other_evaluation_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, submitted_at, status)
            VALUES (?, 1, CURRENT_TIMESTAMP, 'submitted')
            """,
            (other_evaluation_id,),
        )

        other_response_id = connection.execute(
            """
            SELECT id FROM responses
            WHERE evaluation_id = ? AND student_id = 1
            """,
            (other_evaluation_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, text_value)
            VALUES (?, ?, ?)
            """,
            (
                other_response_id,
                other_question_id,
                "This belongs to another evaluation.",
            ),
        )

    response = api_client.get("/api/evaluations/1/feedback/topics")

    assert response.status_code == 200
    data = response.get_json()

    all_comments = [
        comment
        for topic in data["topics"]
        for comment in topic["comments"]
    ]

    assert "This belongs to another evaluation." not in all_comments

def test_feedback_topic_ranking_order_and_ties(api_client):
    database = api_client.application.config["TEST_DATABASE"]

    # The fixture already contains one Course Content comment.
    add_feedback(database, "The course content is excellent.", 2)
    add_feedback(database, "The course material is useful.", 3)

    add_feedback(database, "The exam is difficult.", 4)
    add_feedback(database, "The test is difficult.", 5)

    add_feedback(database, "The workload is too heavy.", 6)
    add_feedback(database, "The assignments take too much work.", 7)

    add_feedback(database, "The lecturer explains clearly.", 8)

    response = api_client.get(
        "/api/evaluations/1/feedback/topics/ranking"
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["evaluation_id"] == 1

    topics = data["topics"]

    # Counts must be sorted from highest to lowest.
    counts = [topic["count"] for topic in topics]
    assert counts == sorted(counts, reverse=True)

    course_content = next(
        topic for topic in topics if topic["topic"] == "Course Content"
    )
    assessment = next(
        topic for topic in topics if topic["topic"] == "Assessment"
    )
    workload = next(
        topic for topic in topics if topic["topic"] == "Workload"
    )
    teaching = next(
        topic for topic in topics if topic["topic"] == "Teaching Delivery"
    )

    # Course Content has the highest frequency.
    assert course_content["count"] == 3
    assert course_content["rank"] == 1

    # Assessment and Workload are tied.
    assert assessment["count"] == 2
    assert workload["count"] == 2
    assert assessment["rank"] == 2
    assert workload["rank"] == 2

    # Competition ranking skips rank 3 after the tie.
    assert teaching["count"] == 1
    assert teaching["rank"] == 4

def test_feedback_topic_ranking_returns_all_topics(api_client):
    response = api_client.get(
        "/api/evaluations/1/feedback/topics/ranking"
    )

    assert response.status_code == 200

    topics = response.get_json()["topics"]
    topic_names = {topic["topic"] for topic in topics}

    assert topic_names == {
        "Course Content",
        "Teaching Delivery",
        "Workload",
        "Assessment",
        "Other",
    }

    for topic in topics:
        assert isinstance(topic["count"], int)
        assert isinstance(topic["rank"], int)


def test_feedback_topic_ranking_invalid_evaluation(api_client):
    response = api_client.get(
        "/api/evaluations/9999/feedback/topics/ranking"
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "EVALUATION_NOT_FOUND"


def test_feedback_topic_ranking_excludes_other_evaluations(api_client):
    database = api_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (1, 1, 'Another Evaluation', '2099-01-01 00:00:00', 'open')
            """
        )

        other_evaluation_id = connection.execute(
            "SELECT id FROM evaluations WHERE title = ?",
            ("Another Evaluation",),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (?, 'Other feedback', 'text', 0, 1)
            """,
            (other_evaluation_id,),
        )

        other_question_id = connection.execute(
            """
            SELECT id FROM questions
            WHERE evaluation_id = ? AND question_type = 'text'
            """,
            (other_evaluation_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, submitted_at, status)
            VALUES (?, 1, CURRENT_TIMESTAMP, 'submitted')
            """,
            (other_evaluation_id,),
        )

        other_response_id = connection.execute(
            """
            SELECT id FROM responses
            WHERE evaluation_id = ? AND student_id = 1
            """,
            (other_evaluation_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, text_value)
            VALUES (?, ?, ?)
            """,
            (
                other_response_id,
                other_question_id,
                "Exam exam exam exam exam.",
            ),
        )

    response = api_client.get(
        "/api/evaluations/1/feedback/topics/ranking"
    )

    assert response.status_code == 200
    topics = response.get_json()["topics"]

    assessment = next(
        topic for topic in topics if topic["topic"] == "Assessment"
    )
    assert assessment["count"] == 0
