
import sqlite3
import unittest
from pathlib import Path


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "schema.sql"
)


class ResponseSchemaTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )

        cursor = self.connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            ("student@example.com", "test-hash", "Test Student", "student"),
        )
        self.student_id = cursor.lastrowid

        cursor = self.connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            ("lecturer@example.com", "test-hash", "Test Lecturer", "lecturer"),
        )
        self.lecturer_id = cursor.lastrowid

        cursor = self.connection.execute(
            """
            INSERT INTO courses (course_code, course_name)
            VALUES (?, ?)
            """,
            ("TEST101", "Test Course"),
        )
        self.course_id = cursor.lastrowid

        cursor = self.connection.execute(
            """
            INSERT INTO evaluations
                (course_id, created_by, title, deadline, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self.course_id,
                self.lecturer_id,
                "Test Evaluation",
                "2026-12-31 23:59:59",
                "open",
            ),
        )
        self.evaluation_id = cursor.lastrowid

        cursor = self.connection.execute(
            """
            INSERT INTO questions
                (evaluation_id, question_text, question_type,
                 is_required, question_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (self.evaluation_id, "Test question", "rating", 1, 1),
        )
        self.question_id = cursor.lastrowid

    def tearDown(self):
        self.connection.close()

    def test_student_cannot_have_duplicate_response(self):
        self.connection.execute(
            """
            INSERT INTO responses (evaluation_id, student_id, status)
            VALUES (?, ?, 'draft')
            """,
            (self.evaluation_id, self.student_id),
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO responses (evaluation_id, student_id, status)
                VALUES (?, ?, 'draft')
                """,
                (self.evaluation_id, self.student_id),
            )

    def test_question_cannot_have_duplicate_answer_in_response(self):
        cursor = self.connection.execute(
            """
            INSERT INTO responses (evaluation_id, student_id, status)
            VALUES (?, ?, 'draft')
            """,
            (self.evaluation_id, self.student_id),
        )
        response_id = cursor.lastrowid

        self.connection.execute(
            """
            INSERT INTO response_answers
                (response_id, question_id, rating_value)
            VALUES (?, ?, ?)
            """,
            (response_id, self.question_id, 4),
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO response_answers
                    (response_id, question_id, rating_value)
                VALUES (?, ?, ?)
                """,
                (response_id, self.question_id, 5),
            )

    def test_submission_status_and_timestamp_are_stored(self):
        self.connection.execute(
            """
            INSERT INTO responses
                (evaluation_id, student_id, status, submitted_at)
            VALUES (?, ?, 'submitted', '2026-10-23 12:00:00')
            """,
            (self.evaluation_id, self.student_id),
        )

        row = self.connection.execute(
            """
            SELECT status, submitted_at
            FROM responses
            WHERE evaluation_id = ? AND student_id = ?
            """,
            (self.evaluation_id, self.student_id),
        ).fetchone()

        self.assertEqual(row[0], "submitted")
        self.assertEqual(row[1], "2026-10-23 12:00:00")


if __name__ == "__main__":
    unittest.main()
