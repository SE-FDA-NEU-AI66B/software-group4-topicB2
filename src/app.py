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

if __name__ == "__main__":
    app.run(debug=True)