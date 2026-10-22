from pathlib import Path
import sqlite3

from flask import Flask, render_template, jsonify, request, session
import os

from datetime import datetime
from flask import session
app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-test-key"
def api_error(status, code, message, action):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "action": action
        }
    }), status

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "data" / "edusurvey.db"


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



@app.route("/api/submissions", methods=["POST"])
def create_submission():
    data = request.get_json(silent=True) or {}

    
    # Require an authenticated session.
    user_id = session.get("user_id")
    if not user_id:
        return api_error(
            401,
            "UNAUTHORIZED",
            "You must be logged in to submit an evaluation.",
            "Log in and try again."
        )

    data = request.get_json(silent=True) or {}
    evaluation_id = data.get("evaluation_id")
    answers = data.get("answers")

    if not isinstance(answers, dict) or not answers:
        return api_error(
            400,
            "MISSING_REQUIRED_ANSWERS",
            "Required answers are missing.",
            "Complete all required questions and try again."
        )

    if not evaluation_id:
        return api_error(
            400,
            "INVALID_EVALUATION",
            "An evaluation ID is required.",
            "Select an evaluation and try again."
        )

    with get_db_connection() as connection:
        evaluation = connection.execute(
            """
            SELECT deadline, status
            FROM evaluations
            WHERE id = ?
            """,
            (evaluation_id,)
        ).fetchone()

        if evaluation is None:
            return api_error(
                404,
                "EVALUATION_NOT_FOUND",
                "The evaluation does not exist.",
                "Select an available evaluation."
            )

        deadline = datetime.fromisoformat(evaluation["deadline"])
        if deadline < datetime.now():
            return api_error(
                400,
                "DEADLINE_EXPIRED",
                "The submission deadline has passed.",
                "Contact the lecturer if you need further assistance."
            )

        if evaluation["status"] != "open":
            return api_error(
                400,
                "EVALUATION_CLOSED",
                "This evaluation is not open for submissions.",
                "Choose an open evaluation."
            )

        existing = connection.execute(
            """
            SELECT id
            FROM responses
            WHERE evaluation_id = ? AND student_id = ?
              AND status = 'submitted'
            """,
            (evaluation_id, user_id)
        ).fetchone()

        if existing:
            return api_error(
                409,
                "DUPLICATE_SUBMISSION",
                "You have already submitted this evaluation.",
                "Check your submission status instead of submitting again."
            )

    return jsonify({
        "message": "Validation passed. Submission processing is not implemented yet."
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
                        WHEN ra.rating_value BETWEEN 1 AND 5
                        THEN ra.rating_value
                    END
                ) AS rating_count,
                AVG(
                    CASE
                        WHEN ra.rating_value BETWEEN 1 AND 5
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


if __name__ == "__main__":
    app.run(debug=True)