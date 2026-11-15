"""Read-only SQLite verification and logical comparison for isolated restore drills."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

TABLES = (
    "users", "courses", "course_enrollments", "course_lecturers", "evaluations",
    "questions", "responses", "response_answers", "deadline_reminders",
)


def verify_database(database, compare=None):
    """Validate without creating a missing file; never print account/answer data."""
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise sqlite3.DatabaseError("Database integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise sqlite3.IntegrityError("Database foreign-key check failed")
        counts = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        if compare is not None:
            with closing(sqlite3.connect(Path(compare).resolve().as_uri() + "?mode=ro", uri=True)) as restored:
                # Compare schema, sequences and every application row, not just counts.
                # Both files must be isolated/offline so the comparison is stable.
                if list(db.iterdump()) != list(restored.iterdump()):
                    raise ValueError("Restored database differs from the source snapshot")
        return {"integrity": "ok", "foreign_keys": "ok", "table_counts": counts,
                "comparison": "equal" if compare is not None else "not requested"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--compare", type=Path, help="Offline restored copy to compare against this snapshot.")
    args = parser.parse_args()
    print(json.dumps(verify_database(args.database, args.compare), sort_keys=True))


if __name__ == "__main__":
    main()
