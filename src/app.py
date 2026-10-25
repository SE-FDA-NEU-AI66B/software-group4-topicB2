
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request, session
from werkzeug.security import check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "EDUSURVEY_SECRET_KEY",
    "dev-only-secret-change-before-deployment",
)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "data" / "edusurvey.db"


def api_error(status, code, message, action):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "action": action,
        }
    }), status


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


VALID_ROLES = {"student", "lecturer", "administrator"}


def login_required(roles=None):
    allowed_roles = set(roles) if roles is not None else None

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return api_error(
                    401,
                    "UNAUTHORIZED",
                    "You must be logged in to access this resource.",
                    "Log in and try again.",
                )

            if (
                allowed_roles is not None
                and session.get("role") not in allowed_roles
            ):
                return api_error(
                    403,
                    "FORBIDDEN",
                    "You do not have permission to access this resource.",
                    "Log in with an account that has the required role.",
                )

            return view(*args, **kwargs)

        return wrapped

    return decorator


@app.route("/api/evaluations", methods=["GET"])
@login_required(roles=["student"])
def get_student_evaluations():
    student_id = session.get("user_id")
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.title AS survey_title,
                c.course_name,
                lecturer.full_name AS lecturer_name,
                e.deadline AS submission_deadline,
                e.status AS evaluation_status,
                EXISTS (
                    SELECT 1
                    FROM responses AS r
                    WHERE r.evaluation_id = e.id
                      AND r.student_id = ?
                      AND r.status = 'submitted'
                ) AS is_completed
            FROM evaluations AS e
            JOIN courses AS c
                ON c.id = e.course_id
            JOIN course_enrollments AS ce
                ON ce.course_id = c.id
            LEFT JOIN course_lecturers AS cl
                ON cl.course_id = c.id
            LEFT JOIN users AS lecturer
                ON lecturer.id = cl.lecturer_id
            WHERE ce.student_id = ?
              AND LOWER(e.status) IN ('open', 'closed')
            ORDER BY e.deadline ASC, e.id ASC
            """,
            (student_id, student_id),
        ).fetchall()

        now = datetime.now()
        evaluations = []

        for row in rows:
            deadline_text = row["submission_deadline"]
            deadline = None

            if deadline_text:
                try:
                    deadline = datetime.fromisoformat(deadline_text)
                except (ValueError, TypeError):
                    deadline = None

            evaluation_status = (
                row["evaluation_status"] or ""
            ).lower()

            if row["is_completed"]:
                survey_status = "Completed"

            elif evaluation_status == "closed":
                survey_status = "Closed"

            elif deadline is not None and deadline <= now:
                survey_status = "Closed"

            elif (
                deadline is not None
                and deadline <= now + timedelta(days=3)
            ):
                survey_status = "Due soon"

            else:
                survey_status = "Active"

            evaluations.append({
                "survey_title": row["survey_title"],
                "course_name": row["course_name"],
                "lecturer_name": row["lecturer_name"],
                "submission_deadline": deadline_text,
                "survey_status": survey_status,
            })

        return jsonify({
            "evaluations": evaluations,
            "count": len(evaluations),
        }), 200

    finally:
        connection.close()


@app.route("/api/evaluations", methods=["POST"])
def create_evaluation():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return api_error(
            400,
            "INVALID_REQUEST",
            "A JSON object is required.",
            "Send the evaluation details as JSON.",
        )

    deadline_value = data.get("deadline")

    if not isinstance(deadline_value, str) or not deadline_value.strip():
        return api_error(
            400,
            "MISSING_DEADLINE",
            "An evaluation deadline is required.",
            "Provide a valid deadline.",
        )

    deadline_value = deadline_value.strip()

    try:
        parsed_deadline = datetime.fromisoformat(
            deadline_value.replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return api_error(
            400,
            "INVALID_DEADLINE",
            "The evaluation deadline is invalid.",
            "Use an ISO 8601 date and time.",
        )

    # Store a consistent ISO timestamp, preserving timezone if supplied.
    deadline_to_store = parsed_deadline.isoformat()

    course_id = data.get("course_id")
    title = data.get("title")
    questions = data.get("questions")

    if (
        isinstance(course_id, bool)
        or not isinstance(course_id, int)
        or course_id <= 0
    ):
        return api_error(
            400,
            "INVALID_COURSE",
            "A valid course ID is required.",
            "Select a valid course.",
        )

    if not isinstance(title, str) or not title.strip():
        return api_error(
            400,
            "INVALID_TITLE",
            "An evaluation title is required.",
            "Provide a title.",
        )

    if not isinstance(questions, list) or not questions:
        return api_error(
            400,
            "INVALID_QUESTIONS",
            "At least one question is required.",
            "Add one or more questions.",
        )

    for question in questions:
        if not isinstance(question, dict):
            return api_error(
                400,
                "INVALID_QUESTION",
                "Each question must be an object.",
                "Check the question data.",
            )

        question_text = question.get("question_text")
        question_type = question.get("question_type")
        is_required = question.get("is_required", False)

        if not isinstance(question_text, str) or not question_text.strip():
            return api_error(
                400,
                "INVALID_QUESTION",
                "Question text is required.",
                "Provide text for every question.",
            )

        if question_type not in ("rating", "text"):
            return api_error(
                400,
                "INVALID_QUESTION_TYPE",
                "The question type is invalid.",
                "Use 'rating' or 'text'.",
            )

        if not isinstance(is_required, bool):
            return api_error(
                400,
                "INVALID_QUESTION",
                "is_required must be a boolean.",
                "Use true or false for is_required.",
            )

    user_id = session.get("user_id")

    if not user_id:
        return api_error(
            401,
            "UNAUTHORIZED",
            "You must be logged in.",
            "Log in and try again.",
        )

    try:
        with get_db_connection() as connection:
            user = connection.execute(
                "SELECT role FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

            if user is None:
                return api_error(
                    401,
                    "UNAUTHORIZED",
                    "The logged-in user does not exist.",
                    "Log in again.",
                )

            if user["role"] != "lecturer":
                return api_error(
                    403,
                    "FORBIDDEN",
                    "Only lecturers can create evaluations.",
                    "Log in with a lecturer account.",
                )

            course = connection.execute(
                "SELECT id FROM courses WHERE id = ?",
                (course_id,),
            ).fetchone()

            if course is None:
                return api_error(
                    404,
                    "COURSE_NOT_FOUND",
                    "The course does not exist.",
                    "Select an existing course.",
                )

            assignment = connection.execute(
                """
                SELECT 1
                FROM course_lecturers
                WHERE lecturer_id = ? AND course_id = ?
                """,
                (user_id, course_id),
            ).fetchone()

            if assignment is None:
                return api_error(
                    403,
                    "FORBIDDEN",
                    "You are not assigned to this course.",
                    "Choose a course assigned to you.",
                )

            # Create the evaluation and its questions in one transaction.
            connection.execute("BEGIN")

            cursor = connection.execute(
                """
                INSERT INTO evaluations
                    (course_id, created_by, title, deadline, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    course_id,
                    session["user_id"],
                    title.strip(),
                    deadline_to_store,
                    "draft",
                ),
            )
            evaluation_id = cursor.lastrowid

            for index, question in enumerate(questions, start=1):
                connection.execute(
                    """
                    INSERT INTO questions (
                        evaluation_id,
                        question_text,
                        question_type,
                        is_required,
                        question_order
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        evaluation_id,
                        question["question_text"].strip(),
                        question["question_type"],
                        int(question.get("is_required", False)),
                        index,
                    ),
                )

            connection.commit()

    except sqlite3.Error:
        app.logger.exception("Failed to create evaluation")
        return api_error(
            500,
            "EVALUATION_CREATION_FAILED",
            "The evaluation could not be created.",
            "Please try again later.",
        )

    return jsonify({
        "message": "Evaluation created successfully.",
        "evaluation_id": evaluation_id,
        "questions_created": len(questions),
        "status": "open",
    }), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return api_error(
            400,
            "INVALID_REQUEST",
            "A valid JSON object is required.",
            "Send email and password as JSON.",
        )

    email = data.get("email")
    password = data.get("password")

    if (
        not isinstance(email, str)
        or not isinstance(password, str)
        or not email.strip()
        or not password
    ):
        return api_error(
            400,
            "MISSING_CREDENTIALS",
            "Email and password are required.",
            "Provide both email and password.",
        )

    email = email.strip().lower()

    with get_db_connection() as connection:
        user = connection.execute(
            """
            SELECT id, email, password_hash, full_name, role
            FROM users
            WHERE lower(email) = ?
            """,
            (email,),
        ).fetchone()

    if (
        user is None
        or user["role"] not in VALID_ROLES
        or not check_password_hash(user["password_hash"], password)
    ):
        return api_error(
            401,
            "INVALID_CREDENTIALS",
            "Email or password is incorrect.",
            "Check your credentials and try again.",
        )

    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]

    return jsonify({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }), 200


@app.route("/api/auth/me", methods=["GET"])
@login_required()
def current_user():
    with get_db_connection() as connection:
        user = connection.execute(
            """
            SELECT id, email, full_name, role
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],),
        ).fetchone()

    if user is None:
        session.clear()
        return api_error(
            401,
            "UNAUTHORIZED",
            "The authenticated user no longer exists.",
            "Log in again with a valid account.",
        )

    return jsonify({
        "authenticated": True,
        "user": dict(user),
    }), 200


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"authenticated": False}), 200


def classify_feedback(comment):
    """Classify a written comment into a supported feedback topic."""
    text = comment.lower()

    topic_keywords = {
        "Course Content": [
            "course content", "course material", "learning material",
            "content", "lecture notes", "slides", "syllabus",
        ],
        "Teaching Delivery": [
            "teaching", "lecturer", "teacher", "explanation",
            "explained", "presentation", "delivery", "lecture",
        ],
        "Workload": [
            "workload", "work load", "too much work", "heavy workload",
            "assignments", "assignment load", "time-consuming",
        ],
        "Assessment": [
            "assessment", "exam", "examination", "test", "grading",
            "marking", "quiz", "feedback on grades",
        ],
    }

    for topic, keywords in topic_keywords.items():
        if any(keyword in text for keyword in keywords):
            return topic

    return "Other"


@app.route("/")
def home():
    return '<h1>EduSurvey</h1><a href="/evaluations">View Evaluations</a>'


@app.route("/evaluations")
def evaluations():
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.title,
                e.deadline,
                e.status,
                c.course_code,
                c.course_name
            FROM evaluations AS e
            JOIN courses AS c ON c.id = e.course_id
            ORDER BY e.deadline, e.id
            """
        ).fetchall()

    return render_template("evaluations.html", evaluations=rows)


@app.route("/lecturer/feedback")
@login_required(roles=["lecturer"])
def lecturer_feedback_list():
    """List evaluations belonging to courses assigned to this lecturer."""
    lecturer_id = session["user_id"]

    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.title,
                e.deadline,
                e.status,
                c.id AS course_id,
                c.course_code,
                c.course_name,
                COUNT(
                    DISTINCT CASE
                        WHEN r.status = 'submitted' THEN r.id
                    END
                ) AS completed_responses
            FROM evaluations AS e
            JOIN courses AS c ON c.id = e.course_id
            JOIN course_lecturers AS cl
              ON cl.course_id = c.id
             AND cl.lecturer_id = ?
            LEFT JOIN responses AS r
              ON r.evaluation_id = e.id
            GROUP BY e.id, c.id
            ORDER BY e.created_at DESC, e.id DESC
            """,
            (lecturer_id,),
        ).fetchall()

    return render_template(
        "lecturer_feedback.html",
        evaluations=rows,
        selected_evaluation=None,
        completed_responses=0,
        average_rating=None,
        rating_count=0,
        ratings=[],
        comments=[],
        error_message=None,
    )


@app.route("/lecturer/feedback/<int:evaluation_id>")
@login_required(roles=["lecturer"])
def lecturer_feedback_detail(evaluation_id):
    """Show submitted ratings and written feedback for an assigned course."""
    lecturer_id = session["user_id"]

    with get_db_connection() as connection:
        evaluation = connection.execute(
            """
            SELECT
                e.id,
                e.title,
                e.deadline,
                e.status,
                c.id AS course_id,
                c.course_code,
                c.course_name
            FROM evaluations AS e
            JOIN courses AS c ON c.id = e.course_id
            JOIN course_lecturers AS cl
              ON cl.course_id = c.id
             AND cl.lecturer_id = ?
            WHERE e.id = ?
            """,
            (lecturer_id, evaluation_id),
        ).fetchone()

        # Return 404 for nonexistent evaluations and evaluations
        # belonging to courses the lecturer is not assigned to.
        if evaluation is None:
            return (
                render_template(
                    "lecturer_feedback.html",
                    evaluations=[],
                    selected_evaluation=None,
                    completed_responses=0,
                    average_rating=None,
                    rating_count=0,
                    ratings=[],
                    comments=[],
                    error_message=(
                        "Evaluation not found or you do not have "
                        "permission to view it."
                    ),
                ),
                404,
            )

        completed_responses = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM responses
            WHERE evaluation_id = ?
              AND status = 'submitted'
            """,
            (evaluation_id,),
        ).fetchone()["total"]

        ratings = connection.execute(
            """
            SELECT
                q.question_text,
                ra.rating_value,
                r.submitted_at
            FROM questions AS q
            JOIN response_answers AS ra
              ON ra.question_id = q.id
            JOIN responses AS r
              ON r.id = ra.response_id
            WHERE q.evaluation_id = ?
              AND q.question_type = 'rating'
              AND r.evaluation_id = q.evaluation_id
              AND r.status = 'submitted'
              AND ra.rating_value BETWEEN 1 AND 5
            ORDER BY r.submitted_at DESC, r.id DESC, q.question_order
            """,
            (evaluation_id,),
        ).fetchall()

        comments = connection.execute(
            """
            SELECT
                q.question_text,
                ra.text_value,
                r.submitted_at
            FROM questions AS q
            JOIN response_answers AS ra
              ON ra.question_id = q.id
            JOIN responses AS r
              ON r.id = ra.response_id
            WHERE q.evaluation_id = ?
              AND q.question_type = 'text'
              AND r.evaluation_id = q.evaluation_id
              AND r.status = 'submitted'
              AND ra.text_value IS NOT NULL
              AND TRIM(ra.text_value) != ''
            ORDER BY r.submitted_at DESC, r.id DESC, q.question_order
            """,
            (evaluation_id,),
        ).fetchall()

        rating_summary = connection.execute(
            """
            SELECT
                COUNT(ra.rating_value) AS rating_count,
                AVG(ra.rating_value) AS average_rating
            FROM questions AS q
            JOIN response_answers AS ra
              ON ra.question_id = q.id
            JOIN responses AS r
              ON r.id = ra.response_id
            WHERE q.evaluation_id = ?
              AND q.question_type = 'rating'
              AND r.evaluation_id = q.evaluation_id
              AND r.status = 'submitted'
              AND ra.rating_value BETWEEN 1 AND 5
            """,
            (evaluation_id,),
        ).fetchone()

    average_rating = rating_summary["average_rating"]

    # Include only evaluations belonging to courses assigned to this lecturer.
    with get_db_connection() as connection:
        evaluations_list = connection.execute(
            """
            SELECT
                e.id,
                e.title,
                e.deadline,
                e.status,
                c.course_code,
                c.course_name,
                COUNT(
                    DISTINCT CASE
                        WHEN r.status = 'submitted' THEN r.id
                    END
                ) AS completed_responses
            FROM evaluations AS e
            JOIN courses AS c ON c.id = e.course_id
            JOIN course_lecturers AS cl
              ON cl.course_id = c.id
             AND cl.lecturer_id = ?
            LEFT JOIN responses AS r ON r.evaluation_id = e.id
            GROUP BY e.id, c.id
            ORDER BY e.created_at DESC, e.id DESC
            """,
            (lecturer_id,),
        ).fetchall()

    return render_template(
        "lecturer_feedback.html",
        evaluations=evaluations_list,
        selected_evaluation=evaluation,
        completed_responses=completed_responses,
        average_rating=(
            round(average_rating, 2)
            if average_rating is not None else None
        ),
        rating_count=rating_summary["rating_count"],
        ratings=ratings,
        comments=comments,
        error_message=None,
    )


@app.route("/api/evaluations/<int:evaluation_id>/feedback/topics", methods=["GET"])
def grouped_feedback_by_topic(evaluation_id):
    with get_db_connection() as connection:
        evaluation = connection.execute(
            "SELECT id FROM evaluations WHERE id = ?",
            (evaluation_id,),
        ).fetchone()

        if evaluation is None:
            return api_error(
                404,
                "EVALUATION_NOT_FOUND",
                "The evaluation does not exist.",
                "Select an existing evaluation and try again.",
            )

        rows = connection.execute(
            """
            SELECT ra.text_value
            FROM response_answers AS ra
            JOIN responses AS r ON r.id = ra.response_id
            JOIN questions AS q ON q.id = ra.question_id
            WHERE r.evaluation_id = ?
              AND q.evaluation_id = r.evaluation_id
              AND r.status = 'submitted'
              AND q.question_type = 'text'
              AND ra.text_value IS NOT NULL
              AND TRIM(ra.text_value) != ''
            ORDER BY r.id, q.question_order
            """,
            (evaluation_id,),
        ).fetchall()

    topic_names = [
        "Course Content",
        "Teaching Delivery",
        "Workload",
        "Assessment",
        "Other",
    ]

    grouped = {
        topic: {"topic": topic, "count": 0, "comments": []}
        for topic in topic_names
    }

    for row in rows:
        comment = row["text_value"].strip()
        topic = classify_feedback(comment)
        grouped[topic]["comments"].append(comment)
        grouped[topic]["count"] += 1

    return jsonify({
        "evaluation_id": evaluation_id,
        "topics": list(grouped.values()),
    }), 200


@app.route(
    "/api/evaluations/<int:evaluation_id>/feedback/topics/ranking",
    methods=["GET"],
)
def rank_feedback_topics(evaluation_id):
    """Rank feedback topics by comment frequency."""
    with get_db_connection() as connection:
        evaluation = connection.execute(
            "SELECT id FROM evaluations WHERE id = ?",
            (evaluation_id,),
        ).fetchone()

        if evaluation is None:
            return api_error(
                404,
                "EVALUATION_NOT_FOUND",
                "The evaluation does not exist.",
                "Select an existing evaluation and try again.",
            )

        rows = connection.execute(
            """
            SELECT ra.text_value
            FROM response_answers AS ra
            JOIN responses AS r ON r.id = ra.response_id
            JOIN questions AS q ON q.id = ra.question_id
            WHERE r.evaluation_id = ?
              AND q.evaluation_id = r.evaluation_id
              AND r.status = 'submitted'
              AND q.question_type = 'text'
              AND ra.text_value IS NOT NULL
              AND TRIM(ra.text_value) != ''
            ORDER BY r.id, q.question_order
            """,
            (evaluation_id,),
        ).fetchall()

    topic_names = [
        "Course Content",
        "Teaching Delivery",
        "Workload",
        "Assessment",
        "Other",
    ]

    counts = {topic: 0 for topic in topic_names}

    for row in rows:
        topic = classify_feedback(row["text_value"].strip())
        counts[topic] += 1

    ranked_topics = sorted(
        topic_names,
        key=lambda topic: (-counts[topic], topic),
    )

    topics = []
    previous_count = None
    current_rank = 0

    for position, topic in enumerate(ranked_topics, start=1):
        count = counts[topic]

        if count != previous_count:
            current_rank = position

        topics.append({
            "topic": topic,
            "count": count,
            "rank": current_rank,
        })

        previous_count = count

    return jsonify({
        "evaluation_id": evaluation_id,
        "topics": topics,
    }), 200


@app.route("/api/evaluations/<int:evaluation_id>/statistics", methods=["GET"])
def evaluation_statistics(evaluation_id):
    """Return response count and average rating for each rating question."""
    with get_db_connection() as connection:
        evaluation = connection.execute(
            "SELECT id FROM evaluations WHERE id = ?",
            (evaluation_id,),
        ).fetchone()

        if evaluation is None:
            return api_error(
                404,
                "EVALUATION_NOT_FOUND",
                "The evaluation does not exist.",
                "Select an existing evaluation and try again.",
            )

        completed_responses = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM responses
            WHERE evaluation_id = ?
              AND status = 'submitted'
            """,
            (evaluation_id,),
        ).fetchone()["total"]

        rows = connection.execute(
            """
            SELECT
                q.id AS question_id,
                q.question_text,
                COUNT(
                    CASE
                        WHEN r.id IS NOT NULL
                         AND ra.rating_value BETWEEN 1 AND 5
                        THEN ra.rating_value
                    END
                ) AS rating_count,
                AVG(
                    CASE
                        WHEN r.id IS NOT NULL
                         AND ra.rating_value BETWEEN 1 AND 5
                        THEN ra.rating_value
                    END
                ) AS average_rating
            FROM questions AS q
            LEFT JOIN response_answers AS ra
                ON ra.question_id = q.id
            LEFT JOIN responses AS r
                ON r.id = ra.response_id
               AND r.evaluation_id = q.evaluation_id
               AND r.status = 'submitted'
            WHERE q.evaluation_id = ?
              AND q.question_type = 'rating'
            GROUP BY q.id, q.question_text, q.question_order
            ORDER BY q.question_order, q.id
            """,
            (evaluation_id,),
        ).fetchall()

    question_statistics = []

    for row in rows:
        average = row["average_rating"]
        question_statistics.append({
            "question_id": row["question_id"],
            "question_text": row["question_text"],
            "rating_count": row["rating_count"],
            "average_rating": (
                round(average, 2) if average is not None else None
            ),
        })

    return jsonify({
        "evaluation_id": evaluation_id,
        "completed_responses": completed_responses,
        "question_statistics": question_statistics,
    }), 200


@app.route("/api/submissions", methods=["POST"])
def create_submission():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return api_error(
            400,
            "INVALID_REQUEST",
            "A JSON object is required.",
            "Send the evaluation ID and answers as a JSON object.",
        )

    user_id = session.get("user_id")
    if not user_id:
        return api_error(
            401,
            "UNAUTHORIZED",
            "You must be logged in to submit an evaluation.",
            "Log in and try again.",
        )

    evaluation_id = data.get("evaluation_id")
    answers = data.get("answers")

    if (
        isinstance(evaluation_id, bool)
        or not isinstance(evaluation_id, int)
        or evaluation_id <= 0
    ):
        return api_error(
            400,
            "INVALID_EVALUATION",
            "A valid evaluation ID is required.",
            "Select an evaluation and try again.",
        )

    if not isinstance(answers, dict):
        return api_error(
            400,
            "MISSING_REQUIRED_ANSWERS",
            "Answers must be provided as an object.",
            "Complete all required questions and try again.",
        )

    with get_db_connection() as connection:
        student = connection.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if student is None:
            return api_error(
                401,
                "UNAUTHORIZED",
                "The logged-in user no longer exists.",
                "Log in again and retry.",
            )

        if student["role"] != "student":
            return api_error(
                403,
                "FORBIDDEN",
                "Only students can submit evaluations.",
                "Log in with a student account.",
            )

        evaluation = connection.execute(
            """
            SELECT id, course_id, deadline, status
            FROM evaluations
            WHERE id = ?
            """,
            (evaluation_id,),
        ).fetchone()

        if evaluation is None:
            return api_error(
                404,
                "EVALUATION_NOT_FOUND",
                "The evaluation does not exist.",
                "Select an available evaluation.",
            )

        if evaluation["status"] != "open":
            return api_error(
                400,
                "EVALUATION_CLOSED",
                "This evaluation is not open for submissions.",
                "Choose an open evaluation.",
            )

        try:
            deadline = datetime.fromisoformat(
                evaluation["deadline"].replace("Z", "+00:00")
            )
            now = (
                datetime.now(deadline.tzinfo)
                if deadline.tzinfo
                else datetime.now()
            )
        except (ValueError, TypeError, AttributeError):
            return api_error(
                500,
                "INVALID_EVALUATION_DEADLINE",
                "The evaluation deadline is invalid.",
                "Contact the system administrator.",
            )

        if deadline < now:
            return api_error(
                400,
                "DEADLINE_EXPIRED",
                "The submission deadline has passed.",
                "Contact the lecturer if you need further assistance.",
            )

        enrollment = connection.execute(
            """
            SELECT 1
            FROM course_enrollments
            WHERE student_id = ? AND course_id = ?
            """,
            (user_id, evaluation["course_id"]),
        ).fetchone()

        if enrollment is None:
            return api_error(
                403,
                "NOT_ENROLLED",
                "You are not enrolled in the course for this evaluation.",
                "Only enrolled students can submit this evaluation.",
            )

        questions = connection.execute(
            """
            SELECT id, question_type, is_required
            FROM questions
            WHERE evaluation_id = ?
            ORDER BY question_order
            """,
            (evaluation_id,),
        ).fetchall()

        if not questions:
            return api_error(
                400,
                "NO_QUESTIONS",
                "This evaluation has no questions.",
                "Contact the lecturer responsible for this evaluation.",
            )

        questions_by_id = {
            str(question["id"]): question
            for question in questions
        }

        normalized_answers = {}

        # Validate each submitted answer.
        for question_id, answer in answers.items():
            if (
                not isinstance(question_id, str)
                or not question_id.isdigit()
                or str(int(question_id)) != question_id
                or question_id not in questions_by_id
            ):
                return api_error(
                    400,
                    "INVALID_QUESTION",
                    "An answer refers to an invalid question.",
                    "Only answer questions belonging to this evaluation.",
                )

            if not isinstance(answer, dict):
                return api_error(
                    400,
                    "INVALID_ANSWER",
                    "Each answer must be an object.",
                    "Provide a valid answer for each question.",
                )

            question = questions_by_id[question_id]
            rating_value = answer.get("rating_value")
            text_value = answer.get("text_value")

            if question["question_type"] == "rating":
                if (
                    isinstance(rating_value, bool)
                    or not isinstance(rating_value, int)
                    or not 1 <= rating_value <= 5
                    or text_value is not None
                ):
                    return api_error(
                        400,
                        "INVALID_ANSWER",
                        "Rating answers must be integers from 1 to 5.",
                        "Provide a rating from 1 to 5.",
                    )

                normalized_answers[question_id] = {
                    "rating_value": rating_value,
                    "text_value": None,
                }

            elif question["question_type"] == "text":
                if (
                    not isinstance(text_value, str)
                    or not text_value.strip()
                    or rating_value is not None
                ):
                    return api_error(
                        400,
                        "INVALID_ANSWER",
                        "Text answers must contain non-empty text.",
                        "Enter text for each answered text question.",
                    )

                normalized_answers[question_id] = {
                    "rating_value": None,
                    "text_value": text_value.strip(),
                }

            else:
                return api_error(
                    400,
                    "INVALID_QUESTION_TYPE",
                    "The question has an unsupported type.",
                    "Contact the lecturer responsible for this evaluation.",
                )

        # Required-answer validation must happen before duplicate checking.
        for question in questions:
            question_id = str(question["id"])

            if (
                question["is_required"]
                and question_id not in normalized_answers
            ):
                return api_error(
                    400,
                    "MISSING_REQUIRED_ANSWERS",
                    "One or more required questions are unanswered.",
                    "Complete all required questions and try again.",
                )

        # Check for an existing submission only after validating the payload.
        existing = connection.execute(
            """
            SELECT id, status
            FROM responses
            WHERE evaluation_id = ? AND student_id = ?
            """,
            (evaluation_id, user_id),
        ).fetchone()

        if existing is not None and existing["status"] == "submitted":
            return api_error(
                409,
                "DUPLICATE_SUBMISSION",
                "You have already submitted this evaluation.",
                "Check your submission status instead of submitting again.",
            )

        # Persist the response and answers atomically.
        try:
            connection.execute("BEGIN")

            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO responses
                        (evaluation_id, student_id, submitted_at, status)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 'submitted')
                    """,
                    (evaluation_id, user_id),
                )
                response_id = cursor.lastrowid

            else:
                response_id = existing["id"]

                connection.execute(
                    """
                    UPDATE responses
                    SET submitted_at = CURRENT_TIMESTAMP,
                        status = 'submitted'
                    WHERE id = ?
                    """,
                    (response_id,),
                )

                connection.execute(
                    "DELETE FROM response_answers WHERE response_id = ?",
                    (response_id,),
                )

            for question_id, answer in normalized_answers.items():
                connection.execute(
                    """
                    INSERT INTO response_answers
                        (response_id, question_id, rating_value, text_value)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        response_id,
                        int(question_id),
                        answer["rating_value"],
                        answer["text_value"],
                    ),
                )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()
            return api_error(
                409,
                "DUPLICATE_SUBMISSION",
                "The response conflicts with an existing submission.",
                "Refresh the evaluation and check your submission status.",
            )

        except sqlite3.Error:
            connection.rollback()
            app.logger.exception("Failed to save evaluation submission")
            return api_error(
                500,
                "SUBMISSION_FAILED",
                "The submission could not be saved.",
                "Please try again later.",
            )

    return jsonify({
        "message": "Evaluation submitted successfully.",
        "evaluation_id": evaluation_id,
        "response_id": response_id,
        "status": "submitted",
    }), 201


def close_expired_evaluations(connection):
    """Close open evaluations whose deadlines have passed."""
    connection.execute(
        """
        UPDATE evaluations
        SET status = 'closed'
        WHERE status = 'open'
          AND datetime(deadline) <= datetime('now', 'localtime')
        """
    )


@app.route(
    "/api/evaluations/<int:evaluation_id>/deadline",
    methods=["PUT"],
)
def update_evaluation_deadline(evaluation_id):
    """Allow administrators to update an evaluation deadline."""
    user_id = session.get("user_id")

    if not user_id:
        return api_error(
            401,
            "UNAUTHORIZED",
            "You must be logged in to update an evaluation deadline.",
            "Log in with an administrator account and try again.",
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return api_error(
            400,
            "INVALID_REQUEST",
            "A valid JSON object is required.",
            "Send the new deadline in a JSON object.",
        )

    deadline = data.get("deadline")

    if not isinstance(deadline, str) or not deadline.strip():
        return api_error(
            400,
            "MISSING_DEADLINE",
            "A new deadline is required.",
            "Provide deadline in ISO format.",
        )

    try:
        new_deadline = datetime.fromisoformat(deadline.strip())
    except ValueError:
        return api_error(
            400,
            "INVALID_DEADLINE",
            "The deadline format is invalid.",
            "Use ISO format, for example 2099-12-31T23:59:00.",
        )

    # Compare timezone-aware and timezone-naive datetimes safely.
    if new_deadline.tzinfo is not None:
        now = datetime.now(new_deadline.tzinfo)
    else:
        now = datetime.now()

    if new_deadline <= now:
        return api_error(
            400,
            "DEADLINE_NOT_IN_FUTURE",
            "The new deadline must be in the future.",
            "Provide a future date and time.",
        )

    with get_db_connection() as connection:
        user = connection.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if user is None:
            return api_error(
                401,
                "UNAUTHORIZED",
                "The authenticated user does not exist.",
                "Log in again with a valid account.",
            )

        if user["role"] != "administrator":
            return api_error(
                403,
                "FORBIDDEN",
                "Only administrators can update evaluation deadlines.",
                "Log in with an administrator account.",
            )

        # Close evaluations that have already expired.
        close_expired_evaluations(connection)

        evaluation = connection.execute(
            """
            SELECT id, deadline, status
            FROM evaluations
            WHERE id = ?
            """,
            (evaluation_id,),
        ).fetchone()

        if evaluation is None:
            return api_error(
                404,
                "EVALUATION_NOT_FOUND",
                "The evaluation does not exist.",
                "Select an existing evaluation and try again.",
            )

        if evaluation["status"] == "closed":
            return api_error(
                400,
                "EVALUATION_CLOSED",
                "The evaluation is closed and its deadline cannot be updated.",
                "Create or select an evaluation that is not closed.",
            )

        connection.execute(
            """
            UPDATE evaluations
            SET deadline = ?
            WHERE id = ?
            """,
            (new_deadline.isoformat(), evaluation_id),
        )

    return jsonify({
        "message": "Evaluation deadline updated successfully.",
        "evaluation_id": evaluation_id,
        "deadline": new_deadline.isoformat(),
    }), 200

def send_deadline_reminders(now=None):
    """Record one reminder for each unfinished evaluation due in 24 hours."""
    now = now or datetime.now()
    target_time = now + timedelta(hours=24)

    with get_db_connection() as connection:
        evaluations_due = connection.execute(
            """
            SELECT
                e.id AS evaluation_id,
                e.deadline,
                c.course_name
            FROM evaluations AS e
            JOIN courses AS c ON c.id = e.course_id
            WHERE e.status = 'open'
              AND datetime(e.deadline) >= datetime(?)
              AND datetime(e.deadline) < datetime(?)
              AND EXISTS (
                  SELECT 1
                  FROM course_enrollments AS ce
                  WHERE ce.course_id = e.course_id
              )
              AND EXISTS (
                  SELECT 1
                  FROM responses AS r
                  WHERE r.evaluation_id = e.id
                    AND r.status = 'draft'
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM deadline_reminders AS dr
                  WHERE dr.evaluation_id = e.id
              )
            """,
            (
                (target_time - timedelta(minutes=5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                (target_time + timedelta(minutes=5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            ),
        ).fetchall()

        reminders = []

        for evaluation in evaluations_due:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO deadline_reminders (evaluation_id)
                VALUES (?)
                """,
                (evaluation["evaluation_id"],),
            )

            if cursor.rowcount == 1:
                reminders.append({
                    "evaluation_id": evaluation["evaluation_id"],
                    "course_name": evaluation["course_name"],
                    "deadline": evaluation["deadline"],
                    "message": (
                        f"Reminder: evaluation for "
                        f"{evaluation['course_name']} is due at "
                        f"{evaluation['deadline']}."
                    ),
                })

    return reminders

if __name__ == "__main__":
    app.run(debug=True)
