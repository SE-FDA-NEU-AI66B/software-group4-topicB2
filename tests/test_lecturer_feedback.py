
import re
import sqlite3
from datetime import timedelta

import pytest

import src.app as app_module


def login_as(client, user_id, role):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = role


def connect_db():
    connection = sqlite3.connect(app_module.DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_user(connection, email, full_name, role):
    cursor = connection.execute(
        """
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """,
        (email, "test-password", full_name, role),
    )
    return cursor.lastrowid


def create_response(connection, student_id, status, comment=None):
    cursor = connection.execute(
        """
        INSERT INTO responses (
            evaluation_id, student_id, submitted_at, status
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            1,
            student_id,
            "2026-11-04 10:00:00" if status == "submitted" else None,
            status,
        ),
    )

    response_id = cursor.lastrowid

    if comment is not None:
        question = connection.execute(
            """
            SELECT id
            FROM questions
            WHERE evaluation_id = 1 AND question_type = 'text'
            LIMIT 1
            """
        ).fetchone()

        connection.execute(
            """
            INSERT INTO response_answers (
                response_id, question_id, text_value
            )
            VALUES (?, ?, ?)
            """,
            (response_id, question["id"], comment),
        )

    return response_id


# TC-US04-01
def test_lecturer_can_view_assigned_evaluation_feedback(api_client):
    login_as(api_client, 2, "lecturer")

    response = api_client.get("/lecturer/feedback/1")

    assert response.status_code == 200
    assert b"Test Evaluation" in response.data
    assert b"Completed evaluations" in response.data
    assert b"The course content was very useful." in response.data


# TC-US04-02
def test_lecturer_cannot_view_unassigned_evaluation(api_client):
    connection = connect_db()

    try:
        # Remove the lecturer's assignment to course 1.
        connection.execute(
            """
            DELETE FROM course_lecturers
            WHERE lecturer_id = 2 AND course_id = 1
            """
        )
        connection.commit()
    finally:
        connection.close()

    login_as(api_client, 2, "lecturer")

    # Evaluation 1 exists, but this lecturer is not assigned to its course.
    response = api_client.get("/lecturer/feedback/1")

    assert response.status_code == 403
    assert (
        b"You do not have permission to view this course feedback."
        in response.data
    )


# TC-US04-03
def test_student_cannot_access_lecturer_feedback(api_client):
    login_as(api_client, 1, "student")

    response = api_client.get("/lecturer/feedback")

    assert response.status_code == 403


# TC-US04-04
def test_feedback_page_requires_login(api_client):
    response = api_client.get("/lecturer/feedback/1")

    assert response.status_code == 401


# Additional test: nonexistent evaluation
def test_lecturer_cannot_view_nonexistent_evaluation(api_client):
    login_as(api_client, 2, "lecturer")

    response = api_client.get("/lecturer/feedback/999")

    assert response.status_code == 404


# TC-US04-05
def test_draft_responses_are_excluded_from_feedback(api_client):
    connection = connect_db()

    try:
        student_id = create_user(
            connection,
            "draft@test.com",
            "Draft Student",
            "student",
        )

        create_response(
            connection,
            student_id,
            "draft",
            "DRAFT_ONLY_COMMENT",
        )

        connection.commit()
    finally:
        connection.close()

    login_as(api_client, 2, "lecturer")

    response = api_client.get("/lecturer/feedback/1")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "DRAFT_ONLY_COMMENT" not in html
    assert "The course content was very useful." in html
    assert "Completed evaluations" in html


# TC-US04-06
def test_feedback_displays_submitted_ratings_and_comments(api_client):
    connection = connect_db()

    try:
        response_row = connection.execute(
            """
            SELECT id
            FROM responses
            WHERE evaluation_id = 1 AND student_id = 1
            """
        ).fetchone()

        question = connection.execute(
            """
            SELECT id
            FROM questions
            WHERE evaluation_id = 1 AND question_type = 'rating'
            LIMIT 1
            """
        ).fetchone()

        connection.execute(
            """
            INSERT INTO response_answers (
                response_id, question_id, rating_value
            )
            VALUES (?, ?, ?)
            """,
            (response_row["id"], question["id"], 5),
        )

        connection.commit()
    finally:
        connection.close()

    login_as(api_client, 2, "lecturer")

    response = api_client.get("/lecturer/feedback/1")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "Student ratings" in html
    assert "5 / 5" in html
    assert "Written comments" in html
    assert "The course content was very useful." in html


# TC-US04-07
def test_completed_count_includes_only_submitted_responses(api_client):
    connection = connect_db()

    try:
        submitted_student_id = create_user(
            connection,
            "submitted@test.com",
            "Submitted Student",
            "student",
        )

        create_response(
            connection,
            submitted_student_id,
            "submitted",
            "SECOND_SUBMITTED_COMMENT",
        )

        draft_student_id = create_user(
            connection,
            "another-draft@test.com",
            "Another Draft Student",
            "student",
        )

        create_response(
            connection,
            draft_student_id,
            "draft",
            "ANOTHER_DRAFT_COMMENT",
        )

        connection.commit()
    finally:
        connection.close()

    login_as(api_client, 2, "lecturer")

    response = api_client.get("/lecturer/feedback/1")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "SECOND_SUBMITTED_COMMENT" in html
    assert "ANOTHER_DRAFT_COMMENT" not in html

    # One existing submitted response + one new submitted response.
    assert (
        '<strong>2</strong>' in html
    )


@pytest.mark.parametrize("count", [19, 20, 21], ids=lambda n: f"count-{n}")
def test_feedback_completed_count(api_client, fixed_app_clock, count):
    """#185 / US04 #50: TC-US04-08, TC-37, TC-US04-09; 20 is no cap."""
    submitted_at = (fixed_app_clock - timedelta(hours=2)).isoformat()
    created_at = (fixed_app_clock - timedelta(days=1)).isoformat()
    with sqlite3.connect(app_module.DATABASE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        # Remove the shared fixture's response so N is the entire submitted set.
        connection.execute("DELETE FROM response_answers")
        connection.execute("DELETE FROM responses")
        # SQL CURRENT_TIMESTAMP is independent of the frozen Python clock.
        for table in ("users", "courses", "evaluations"):
            connection.execute(f"UPDATE {table} SET created_at = ?", (created_at,))
        connection.execute("UPDATE course_enrollments SET enrolled_at = ?", (created_at,))
        connection.execute("UPDATE course_lecturers SET assigned_at = ?", (created_at,))
        connection.execute(
            "UPDATE evaluations SET created_by = 2, deadline = ? WHERE id = 1",
            ((fixed_app_clock + timedelta(days=2)).isoformat(),),
        )
        for index in range(count + 1):
            student_id = connection.execute(
                "INSERT INTO users (email, password_hash, full_name, role, created_at) "
                "VALUES (?, ?, ?, 'student', ?)",
                (f"count-{index}@test.com", "test-hash", f"Count Student {index}", created_at),
            ).lastrowid
            connection.execute(
                "INSERT INTO course_enrollments (student_id, course_id, enrolled_at) "
                "VALUES (?, 1, ?)",
                (student_id, created_at),
            )
            response_id = connection.execute(
                "INSERT INTO responses (evaluation_id, student_id, submitted_at, status) "
                "VALUES (1, ?, ?, ?)",
                (student_id, submitted_at if index < count else None,
                 "submitted" if index < count else "draft"),
            ).lastrowid
            connection.execute(
                "INSERT INTO response_answers (response_id, question_id, rating_value) "
                "VALUES (?, 1, 4)",
                (response_id,),
            )
            connection.execute(
                "INSERT INTO response_answers (response_id, question_id, text_value) "
                "VALUES (?, 2, ?)",
                (response_id, f"Submitted comment {index}" if index < count else "COUNT_DRAFT_ONLY"),
            )
        assert connection.execute(
            "SELECT status, COUNT(*) FROM responses GROUP BY status ORDER BY status"
        ).fetchall() == [("draft", 1), ("submitted", count)]

    login_as(api_client, 2, "lecturer")
    response = api_client.get("/api/courses/1/feedback")
    assert response.status_code == 200
    assert response.get_json()["completed_evaluations"] == count
    assert len(response.get_json()["feedback"]) == count
    assert "COUNT_DRAFT_ONLY" not in response.get_data(as_text=True)

    page = api_client.get("/lecturer/feedback/1")
    assert page.status_code == 200
    assert "COUNT_DRAFT_ONLY" not in page.get_data(as_text=True)
    # Bind the number to its label so a rating or unrelated summary cannot match.
    match = re.search(
        r'<span class="muted">Completed evaluations</span>\s*'
        r'<span data-completed-count><strong>(\d+)</strong></span>',
        page.get_data(as_text=True),
    )
    assert match is not None
    assert int(match.group(1)) == response.get_json()["completed_evaluations"]
