
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "edusurvey.db"
SCHEMA_PATH = BASE_DIR / "src" / "schema.sql"


def initialize_database():
    DB_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            connection.executescript(schema_file.read())

        cursor = connection.cursor()

        # Seed users
        users = [
            ("student1@edusurvey.edu", "demo_hash", "Minh Nguyen", "student"),
            ("student2@edusurvey.edu", "demo_hash", "An Tran", "student"),
            ("student3@edusurvey.edu", "demo_hash", "Linh Pham", "student"),
            ("lecturer1@edusurvey.edu", "demo_hash", "Anh Nguyen", "lecturer"),
            ("lecturer2@edusurvey.edu", "demo_hash", "Hoa Le", "lecturer"),
            ("admin@edusurvey.edu", "demo_hash", "Lan Tran", "administrator"),
        ]

        cursor.executemany(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            users,
        )

        # Seed courses
        courses = [
            ("SE101", "Software Engineering"),
            ("AI201", "Artificial Intelligence"),
            ("DB202", "Database Systems"),
            ("WEB203", "Web Development"),
            ("DS204", "Data Structures"),
        ]

        cursor.executemany(
            """
            INSERT INTO courses (course_code, course_name)
            VALUES (?, ?)
            """,
            courses,
        )

        # Seed course enrollments
        enrollments = [
            (1, 1),
            (1, 2),
            (1, 3),
            (2, 1),
            (2, 4),
            (3, 2),
            (3, 5),
        ]

        cursor.executemany(
            """
            INSERT INTO course_enrollments (student_id, course_id)
            VALUES (?, ?)
            """,
            enrollments,
        )

        # Seed lecturer assignments
        lecturer_assignments = [
            (4, 1),
            (4, 2),
            (4, 3),
            (5, 4),
            (5, 5),
        ]

        cursor.executemany(
            """
            INSERT INTO course_lecturers (lecturer_id, course_id)
            VALUES (?, ?)
            """,
            lecturer_assignments,
        )

        # Seed 10 course evaluations
        evaluations = [
            (1, 4, "Software Engineering Mid-Semester Evaluation",
             "2026-10-22 23:59:59", "open"),

            (1, 4, "Software Engineering Final Evaluation",
             "2026-12-15 23:59:59", "draft"),

            (2, 4, "Artificial Intelligence Mid-Semester Evaluation",
             "2026-10-22 23:59:59", "open"),

            (2, 4, "Artificial Intelligence Final Evaluation",
             "2026-12-16 23:59:59", "draft"),

            (3, 4, "Database Systems Course Evaluation",
             "2026-10-25 23:59:59", "open"),

            (3, 4, "Database Systems Final Evaluation",
             "2026-12-18 23:59:59", "draft"),

            (4, 5, "Web Development Mid-Semester Evaluation",
             "2026-10-28 23:59:59", "open"),

            (4, 5, "Web Development Final Evaluation",
             "2026-12-19 23:59:59", "draft"),

            (5, 5, "Data Structures Course Evaluation",
             "2026-10-30 23:59:59", "open"),

            (5, 5, "Data Structures Final Evaluation",
             "2026-12-20 23:59:59", "draft"),
        ]

        cursor.executemany(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            evaluations,
        )

        # Seed questions for every evaluation
        question_templates = [
            (
                "How clearly were the course concepts explained?",
                "rating",
                1,
            ),
            (
                "How useful were the practical exercises?",
                "rating",
                1,
            ),
            (
                "What would you suggest improving in this course?",
                "text",
                0,
            ),
        ]

        evaluation_rows = cursor.execute(
            "SELECT id FROM evaluations ORDER BY id"
        ).fetchall()

        questions_by_evaluation = {}

        for (evaluation_id,) in evaluation_rows:
            questions_by_evaluation[evaluation_id] = []

            for order, (question_text, question_type, required) in enumerate(
                question_templates, start=1
            ):
                cursor.execute(
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
                        question_text,
                        question_type,
                        required,
                        order,
                    ),
                )

                questions_by_evaluation[evaluation_id].append(
                    (cursor.lastrowid, question_type)
                )

        # Seed responses for students enrolled in each course.
        # Only open evaluations receive demo responses.
        open_evaluations = cursor.execute(
            """
            SELECT id, course_id
            FROM evaluations
            WHERE status = 'open'
            ORDER BY id
            """
        ).fetchall()

        for evaluation_id, course_id in open_evaluations:
            students = cursor.execute(
                """
                SELECT u.id
                FROM course_enrollments AS ce
                JOIN users AS u ON u.id = ce.student_id
                WHERE ce.course_id = ?
                  AND u.role = 'student'
                ORDER BY u.id
                """,
                (course_id,),
            ).fetchall()

            for student_index, (student_id,) in enumerate(students):
                # First enrolled student submits a complete response.
                # Other students have a partial draft response.
                is_submitted = student_index == 0

                submitted_at = (
                    "2026-10-18 10:30:00"
                    if is_submitted
                    else None
                )

                response_status = (
                    "submitted" if is_submitted else "draft"
                )

                cursor.execute(
                    """
                    INSERT INTO responses (
                        evaluation_id,
                        student_id,
                        submitted_at,
                        status
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        evaluation_id,
                        student_id,
                        submitted_at,
                        response_status,
                    ),
                )

                response_id = cursor.lastrowid
                questions = questions_by_evaluation[evaluation_id]

                for question_index, (question_id, question_type) in enumerate(
                    questions
                ):
                    # Draft responses contain one partial answer.
                    if not is_submitted and question_index > 0:
                        continue

                    if question_type == "rating":
                        rating_value = (
                            4 + (student_id % 2)
                            if question_index == 0
                            else 3 + (student_id % 3)
                        )
                        text_value = None
                    else:
                        rating_value = None
                        text_value = (
                            "More practical examples would be helpful."
                            if is_submitted
                            else None
                        )

                    cursor.execute(
                        """
                        INSERT INTO response_answers (
                            response_id,
                            question_id,
                            rating_value,
                            text_value
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            response_id,
                            question_id,
                            rating_value,
                            text_value,
                        ),
                    )

        # Verify seeded data before committing.
        counts = {}

        for table in (
            "users",
            "courses",
            "course_enrollments",
            "course_lecturers",
            "evaluations",
            "questions",
            "responses",
            "response_answers",
        ):
            counts[table] = cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        foreign_key_errors = cursor.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise sqlite3.IntegrityError(
                f"Foreign key violations: {foreign_key_errors}"
            )

        connection.commit()

        print("EduSurvey database initialized successfully.")
        print(f"Database: {DB_PATH}")

        for table, count in counts.items():
            print(f"Seeded {table}: {count}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
