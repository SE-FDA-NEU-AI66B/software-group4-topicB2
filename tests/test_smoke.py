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


def login_as_student(client):
    with client.session_transaction() as session:
        session["user_id"] = 1


def login_as_lecturer(client):
    with client.session_transaction() as session:
        session["user_id"] = 2


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


def test_evaluation_statistics_calculates_response_count_and_averages(
    api_client,
):
    database = api_client.application.config["TEST_DATABASE"]

    with sqlite3.connect(database) as connection:
        rating_question_id = connection.execute(
            """
            SELECT id FROM questions
            WHERE evaluation_id = 1 AND question_type = 'rating'
            """
        ).fetchone()[0]

        # Add a rating to the submitted response already created by the fixture.
        response_id = connection.execute(
            """
            SELECT id FROM responses
            WHERE evaluation_id = 1 AND status = 'submitted'
            """
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, rating_value)
            VALUES (?, ?, ?)
            """,
            (response_id, rating_question_id, 4),
        )

        # Add another submitted response with a rating of 2.
        connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, submitted_at, status)
            VALUES (1, 2, CURRENT_TIMESTAMP, 'submitted')
            """
        )
        second_response_id = connection.execute(
            """
            SELECT id FROM responses
            WHERE evaluation_id = 1 AND student_id = 2
            """
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, rating_value)
            VALUES (?, ?, ?)
            """,
            (second_response_id, rating_question_id, 2),
        )
        

    response = api_client.get("/api/evaluations/1/statistics")

    assert response.status_code == 200
    data = response.get_json()
    assert data["completed_responses"] == 2

    stats = data["question_statistics"]
    rating_stat = next(
        item for item in stats
        if item["question_id"] == rating_question_id
    )
    assert rating_stat["rating_count"] == 2
    assert rating_stat["average_rating"] == 3.0


def test_evaluation_statistics_handles_no_ratings(api_client):
    response = api_client.get("/api/evaluations/1/statistics")

    assert response.status_code == 200
    data = response.get_json()

    # The fixture has one submitted response, but no rating answer.
    assert data["completed_responses"] == 1
    rating_stat = data["question_statistics"][0]
    assert rating_stat["rating_count"] == 0
    assert rating_stat["average_rating"] is None


def test_evaluation_statistics_invalid_evaluation(api_client):
    response = api_client.get("/api/evaluations/9999/statistics")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "EVALUATION_NOT_FOUND"


def test_create_evaluation_success(api_client):
    # A lecturer must be logged in to create an evaluation.
    login_as_lecturer(api_client)

    response = api_client.post(
        "/api/evaluations",
        json={
            "course_id": 1,
            "title": "New Evaluation",
            "deadline": "2099-01-01T00:00:00",
            "questions": [
                {
                    "question_text": "Rate the course",
                    "question_type": "rating",
                    "is_required": True,
                },
                {
                    "question_text": "Any suggestions?",
                    "question_type": "text",
                    "is_required": False,
                },
            ],
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["questions_created"] == 2

    database = api_client.application.config["TEST_DATABASE"]
    with sqlite3.connect(database) as connection:
        evaluation = connection.execute(
            "SELECT title, status FROM evaluations WHERE id = ?",
            (data["evaluation_id"],),
        ).fetchone()
        questions = connection.execute(
            "SELECT question_type FROM questions WHERE evaluation_id = ?",
            (data["evaluation_id"],),
        ).fetchall()

    assert evaluation == ("New Evaluation", "draft")
    assert [question[0] for question in questions] == ["rating", "text"]


def test_create_evaluation_requires_deadline(api_client):
    # The endpoint should validate the required deadline before creating data.
    # This request omits the deadline, so it should return a 400 validation error.
    login_as_student(api_client)

    response = api_client.post(
        "/api/evaluations",
        json={
            "course_id": 1,
            "title": "Evaluation without deadline",
            "questions": [
                {
                    "question_text": "Rate the course",
                    "question_type": "rating",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_DEADLINE"


def test_update_evaluation_deadline_success(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 3

    response = api_client.put(
        "/api/evaluations/1/deadline",
        json={"deadline": "2099-12-31T23:59:00"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["evaluation_id"] == 1
    assert data["deadline"] == "2099-12-31T23:59:00"

    database = api_client.application.config["TEST_DATABASE"]
    with sqlite3.connect(database) as connection:
        deadline = connection.execute(
            "SELECT deadline FROM evaluations WHERE id = 1"
        ).fetchone()[0]

    assert deadline == "2099-12-31T23:59:00"


def test_update_evaluation_deadline_requires_login(api_client):
    response = api_client.put(
        "/api/evaluations/1/deadline",
        json={"deadline": "2099-12-31T23:59:00"},
    )

    assert response.status_code == 401


def test_update_evaluation_deadline_forbidden_for_student(api_client):
    login_as_student(api_client)

    response = api_client.put(
        "/api/evaluations/1/deadline",
        json={"deadline": "2099-12-31T23:59:00"},
    )

    assert response.status_code == 403


def test_update_evaluation_deadline_rejects_past_date(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 3

    response = api_client.put(
        "/api/evaluations/1/deadline",
        json={"deadline": "2000-01-01T00:00:00"},
    )

    assert response.status_code == 400
    assert (
        response.get_json()["error"]["code"]
        == "DEADLINE_NOT_IN_FUTURE"
    )


def test_update_evaluation_deadline_requires_deadline(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 3

    response = api_client.put(
        "/api/evaluations/1/deadline",
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_DEADLINE"


def test_update_evaluation_deadline_not_found(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 3

    response = api_client.put(
        "/api/evaluations/9999/deadline",
        json={"deadline": "2099-12-31T23:59:00"},
    )

    assert response.status_code == 404
    assert (
        response.get_json()["error"]["code"]
        == "EVALUATION_NOT_FOUND"
    )

from datetime import datetime, timedelta

from src.app import send_deadline_reminders


def test_deadline_reminder_is_recorded_once(api_client):
    database = api_client.application.config["TEST_DATABASE"]

    now = datetime(2098, 12, 31, 0, 0, 0)
    deadline = now + timedelta(hours=24)

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE evaluations SET deadline = ?, status = 'open' WHERE id = 1",
            (deadline.strftime("%Y-%m-%d %H:%M:%S"),),
        )

        # Mark the existing response as unfinished.
        connection.execute(
            "UPDATE responses SET status = 'draft' WHERE evaluation_id = 1"
        )

        connection.execute(
            """
            INSERT INTO course_enrollments (student_id, course_id)
            VALUES (1, 1)
            """
        )

    first_result = send_deadline_reminders(now)
    second_result = send_deadline_reminders(now)

    assert len(first_result) == 1
    assert first_result[0]["course_name"] == "Test Course"
    assert first_result[0]["deadline"] == deadline.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    assert len(second_result) == 0

    with sqlite3.connect(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM deadline_reminders WHERE evaluation_id = 1"
        ).fetchone()[0]

    assert count == 1
