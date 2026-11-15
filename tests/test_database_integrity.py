"""#189 audit: schema enforcement, runtime findings and real route rollback."""

import sqlite3
from contextlib import closing

import pytest

from src import app as app_module


@pytest.mark.parametrize("parent", ["evaluation", "student", "response", "question"])
def test_schema_rejects_orphans(api_client, parent):
    # Fresh connection: schema-loading PRAGMA does not carry over to this one.
    with closing(sqlite3.connect(app_module.DATABASE)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        before = db.execute("SELECT COUNT(*) FROM responses").fetchone(), db.execute(
            "SELECT COUNT(*) FROM response_answers"
        ).fetchone()
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            if parent in ("evaluation", "student"):
                db.execute(
                    "INSERT INTO responses (evaluation_id, student_id, status) "
                    "VALUES (?, ?, 'draft')",
                    (999 if parent == "evaluation" else 1, 999 if parent == "student" else 1),
                )
            else:
                db.execute(
                    "INSERT INTO response_answers (response_id, question_id, rating_value) "
                    "VALUES (?, ?, 4)",
                    (999 if parent == "response" else 1, 999 if parent == "question" else 1),
                )
        db.rollback()
        after = db.execute("SELECT COUNT(*) FROM responses").fetchone(), db.execute(
            "SELECT COUNT(*) FROM response_answers"
        ).fetchone()
        assert after == before


def test_runtime_foreign_keys_finding(api_client):
    """DB-189-F01: #223 fixed the finding; fresh runtime connections must enforce FK."""
    with closing(app_module.get_db_connection()) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            db.execute(
                "INSERT INTO response_answers (response_id, question_id, rating_value) "
                "VALUES (999, 1, 4)"
            )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        db.rollback()
    with closing(app_module.get_db_connection()) as fresh:
        assert fresh.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert fresh.execute("PRAGMA foreign_key_check").fetchall() == []


def snapshot():
    with closing(sqlite3.connect(app_module.DATABASE)) as db:
        return (
            db.execute("SELECT * FROM responses ORDER BY id").fetchall(),
            db.execute("SELECT * FROM response_answers ORDER BY id").fetchall(),
        )


@pytest.mark.parametrize("existing", [False, True], ids=["new", "draft"])
def test_submission_write_failure_rolls_back(api_client, fixed_app_clock, monkeypatch, existing):
    original_connect = app_module.get_db_connection

    def controlled_connection():
        db = original_connect()
        # Freeze the SQL clock as well as Python; leave production FK settings intact.
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        db.create_function("current_timestamp", 0, lambda: fixed_app_clock.isoformat())
        return db

    monkeypatch.setattr(app_module, "get_db_connection", controlled_connection)
    with closing(sqlite3.connect(app_module.DATABASE)) as db, db:
        db.execute("PRAGMA foreign_keys = ON")
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        db.execute("DELETE FROM response_answers")
        db.execute("DELETE FROM responses")
        if existing:
            db.execute(
                "INSERT INTO responses (id, evaluation_id, student_id, status) "
                "VALUES (1, 1, 1, 'draft')"
            )
            db.execute(
                "INSERT INTO response_answers (response_id, question_id, rating_value) "
                "VALUES (1, 1, 2)"
            )
            db.execute(
                "INSERT INTO response_answers (response_id, question_id, text_value) "
                "VALUES (1, 2, 'Original draft')"
            )
        # ABORT cancels only this statement. The route must roll back prior writes.
        # This fires only after the first replacement answer was actually written.
        db.execute("""
            CREATE TRIGGER injected_answer_failure BEFORE INSERT ON response_answers
            WHEN NEW.question_id = 2 AND EXISTS (
                SELECT 1 FROM response_answers
                WHERE response_id = NEW.response_id AND question_id = 1 AND rating_value = 5
            )
            BEGIN SELECT RAISE(ABORT, 'injected second answer failure'); END
        """)
    before = snapshot()
    with api_client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "student"
    # #223 now sanitizes SQLite errors while the transaction still rolls back.
    failure = api_client.post("/api/submissions", json={
        "evaluation_id": 1,
        "answers": {"1": {"rating_value": 5}, "2": {"text_value": "Replacement"}},
    })
    assert failure.status_code == 503
    assert failure.get_json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "injected second answer failure" not in failure.get_data(as_text=True)
    assert snapshot() == before
    # Remove only the injection, then prove a normal retry can commit all writes.
    with closing(sqlite3.connect(app_module.DATABASE)) as db, db:
        db.execute("DROP TRIGGER injected_answer_failure")
    response = api_client.post("/api/submissions", json={
        "evaluation_id": 1,
        "answers": {"1": {"rating_value": 5}, "2": {"text_value": "Replacement"}},
    })
    assert response.status_code == 201
    responses, answers = snapshot()
    assert len(responses) == 1
    assert responses[0][3:] == (fixed_app_clock.isoformat(), "submitted")
    assert [(row[2], row[3], row[4]) for row in answers] == [
        (1, 5, None), (2, None, "Replacement"),
    ]
