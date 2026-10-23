
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request, session

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-test-key"

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
    data = request.get_json(silent=True) or {}

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

    if not isinstance(answers, dict) or not answers:
        return api_error(
            400,
            "MISSING_REQUIRED_ANSWERS",
            "Required answers are missing.",
            "Complete all required questions and try again.",
        )

    if not evaluation_id:
        return api_error(
            400,
            "INVALID_EVALUATION",
            "An evaluation ID is required.",
            "Select an evaluation and try again.",
        )

    with get_db_connection() as connection:
        evaluation = connection.execute(
            """
            SELECT deadline, status
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

        deadline = datetime.fromisoformat(evaluation["deadline"])

        if deadline < datetime.now():
            return api_error(
                400,
                "DEADLINE_EXPIRED",
                "The submission deadline has passed.",
                "Contact the lecturer if you need further assistance.",
            )

        if evaluation["status"] != "open":
            return api_error(
                400,
                "EVALUATION_CLOSED",
                "This evaluation is not open for submissions.",
                "Choose an open evaluation.",
            )

        existing = connection.execute(
            """
            SELECT id
            FROM responses
            WHERE evaluation_id = ?
              AND student_id = ?
              AND status = 'submitted'
            """,
            (evaluation_id, user_id),
        ).fetchone()

        if existing:
            return api_error(
                409,
                "DUPLICATE_SUBMISSION",
                "You have already submitted this evaluation.",
                "Check your submission status instead of submitting again.",
            )

    return jsonify({
        "message": (
            "Validation passed. Submission processing is not implemented yet."
        )
    }), 200


@app.route("/api/evaluations", methods=["POST"])
def create_evaluation():
    data = request.get_json(silent=True)

    # Validate request body.
    if not isinstance(data, dict):
        return api_error(
            400,
            "INVALID_REQUEST",
            "A valid JSON object is required.",
            "Send evaluation details as a JSON object.",
        )

    course_id = data.get("course_id")
    title = data.get("title")
    deadline = data.get("deadline")
    questions = data.get("questions")

    # Validate course ID.
    if (
        isinstance(course_id, bool)
        or not isinstance(course_id, int)
        or course_id <= 0
    ):
        return api_error(
            400,
            "INVALID_COURSE_ID",
            "Course ID must be a positive integer.",
            "Provide a valid course_id.",
        )

    # Validate title.
    if not isinstance(title, str) or not title.strip():
        return api_error(
            400,
            "MISSING_TITLE",
            "Evaluation title is required.",
            "Provide a non-empty title.",
        )

    # Validate deadline.
    if not isinstance(deadline, str) or not deadline.strip():
        return api_error(
            400,
            "MISSING_DEADLINE",
            "Evaluation deadline is required.",
            "Provide a deadline in ISO format.",
        )

    try:
        parsed_deadline = datetime.fromisoformat(deadline.strip())
    except ValueError:
        return api_error(
            400,
            "INVALID_DEADLINE",
            "The deadline format is invalid.",
            "Use ISO format, for example 2099-01-01T00:00:00.",
        )

    # Validate questions.
    if not isinstance(questions, list) or not questions:
        return api_error(
            400,
            "MISSING_QUESTIONS",
            "At least one question is required.",
            "Provide a non-empty questions list.",
        )

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            return api_error(
                400,
                "INVALID_QUESTION",
                f"Question {index} must be an object.",
                "Provide question_text, question_type, and optionally is_required.",
            )

        question_text = question.get("question_text")
        question_type = question.get("question_type")
        is_required = question.get("is_required", True)

        if not isinstance(question_text, str) or not question_text.strip():
            return api_error(
                400,
                "INVALID_QUESTION_TEXT",
                f"Question {index} requires non-empty question_text.",
                "Provide text for every question.",
            )

        if question_type not in ("rating", "text"):
            return api_error(
                400,
                "INVALID_QUESTION_TYPE",
                f"Question {index} has an unsupported question_type.",
                "Use 'rating' or 'text'.",
            )

        if not isinstance(is_required, bool):
            return api_error(
                400,
                "INVALID_IS_REQUIRED",
                f"Question {index} has an invalid is_required value.",
                "Use true or false.",
            )

    # Authenticate user.
    user_id = session.get("user_id")

    if not user_id:
        return api_error(
            401,
            "UNAUTHORIZED",
            "You must be logged in to create an evaluation.",
            "Log in and try again.",
        )

    # Verify lecturer role, course, and assignment.
    with get_db_connection() as connection:
        user = connection.execute(
            "SELECT id, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if user is None:
            return api_error(
                401,
                "UNAUTHORIZED",
                "The authenticated user does not exist.",
                "Log in again with a valid account.",
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
                "COURSE_ACCESS_DENIED",
                "You are not assigned to this course.",
                "Select a course assigned to your lecturer account.",
            )

        # Insert evaluation and questions in one transaction.
        cursor = connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (?, ?, ?, ?, 'draft')
            """,
            (
                course_id,
                user_id,
                title.strip(),
                parsed_deadline.isoformat(),
            ),
        )

        evaluation_id = cursor.lastrowid

        for order, question in enumerate(questions, start=1):
            connection.execute(
                """
                INSERT INTO questions
                    (evaluation_id, question_text, question_type,
                     is_required, question_order)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    evaluation_id,
                    question["question_text"].strip(),
                    question["question_type"],
                    int(question.get("is_required", True)),
                    order,
                ),
            )

    return jsonify({
        "message": "Evaluation created successfully.",
        "evaluation_id": evaluation_id,
        "course_id": course_id,
        "title": title.strip(),
        "deadline": parsed_deadline.isoformat(),
        "status": "draft",
        "questions_created": len(questions),
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
