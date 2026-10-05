from pathlib import Path
import sqlite3

from flask import Flask, render_template

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True)