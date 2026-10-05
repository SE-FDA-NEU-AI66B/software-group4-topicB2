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

        # Seed course enrolments
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
             "2026-10-20 23:59:59", "open"),

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

        connection.commit()

        evaluation_count = cursor.execute(
            "SELECT COUNT(*) FROM evaluations"
        ).fetchone()[0]

        print("EduSurvey database initialized successfully.")
        print(f"Database: {DB_PATH}")
        print(f"Seeded evaluations: {evaluation_count}")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()