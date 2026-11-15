"""Provision only a missing, explicitly opted-in demo DB at service startup."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask

from src.runtime import configure_runtime


def prepare_database():
    if os.environ.get("EDUSURVEY_ENV") != "production":
        raise RuntimeError("Startup preparation requires production configuration.")
    database = configure_runtime(Flask(__name__), "unused.db")
    mount = Path(os.environ.get("EDUSURVEY_DATA_MOUNT", ""))
    if not mount.is_absolute() or not os.path.ismount(mount) or database.parent.resolve() != mount.resolve():
        raise RuntimeError("Database must be directly on the configured persistent mount.")
    marker = mount / ".edusurvey-provisioned"
    if not database.exists():
        if marker.exists():
            raise RuntimeError("Previously provisioned database missing; restore backup instead of reseeding.")
        if os.environ.get("EDUSURVEY_BOOTSTRAP_DEMO") != "1":
            raise RuntimeError("Database missing; explicit demo bootstrap opt-in required.")
        # Configure imported initializer for this path; never use its development default.
        from src import init_db
        original_path, original_directory = init_db.DB_PATH, init_db.DB_DIR
        try:
            init_db.DB_PATH = database
            init_db.DB_DIR = database.parent
            init_db.initialize_database(m5_demo=True)
        finally:
            init_db.DB_PATH, init_db.DB_DIR = original_path, original_directory
    # Existing empty/corrupt/incomplete data must fail instead of being reset/reseeded.
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        for table in ("users", "courses", "course_enrollments", "course_lecturers",
                      "evaluations", "questions", "responses", "response_answers"):
            db.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
        if db.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok":
            raise RuntimeError("Database integrity check failed.")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Database foreign-key check failed.")
    marker.touch(exist_ok=True)
    print("Production database ready; existing data preserved.")


if __name__ == "__main__":
    prepare_database()
