"""US13 #198 / US08 #38: shared creator authorization and atomic persistence."""

import sqlite3
from contextlib import closing

import pytest

from src import app as module


def payload(count=5):
    return {"course_id": 1, "title": "  New course evaluation  ", "deadline": "2026-11-06T12:00:00+00:00",
            "questions": [{"question_text": f" Question {i} ", "question_type": "rating" if i % 2 else "text",
                           "is_required": i % 2 == 1} for i in range(1, count + 1)]}


def login(client, user_id, role="lecturer"):
    with client.session_transaction() as session:
        session["user_id"], session["role"] = user_id, role


def snapshot():
    with closing(sqlite3.connect(module.DATABASE)) as db:
        return {table: db.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
                for table in ("evaluations", "questions", "users", "courses", "course_enrollments")}


@pytest.mark.parametrize("count", [0, 1, 5, 6], ids=lambda n: f"questions-{n}")
def test_creation_question_count(api_client, count):
    login(api_client, 2)
    before = snapshot()
    response = api_client.post("/api/evaluations", json=payload(count))
    if count == 0:
        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "MISSING_QUESTIONS"
        assert snapshot() == before
        return
    assert response.status_code == 201
    data = response.get_json()
    assert data["questions_created"] == count and len(data["questions"]) == count
    with closing(sqlite3.connect(module.DATABASE)) as db:
        assert db.execute("SELECT course_id,created_by,title,deadline,status FROM evaluations WHERE id=?",
                          (data["evaluation_id"],)).fetchone() == (1, 2, "New course evaluation", payload()["deadline"], "draft")
        actual = db.execute("SELECT id,question_text,question_type,is_required,question_order FROM questions "
                            "WHERE evaluation_id=? ORDER BY question_order", (data["evaluation_id"],)).fetchall()
    assert [(q[1], q[2], bool(q[3]), q[4]) for q in actual] == [
        (f"Question {i}", "rating" if i % 2 else "text", i % 2 == 1, i) for i in range(1, count + 1)]
    assert [q["id"] for q in data["questions"]] == [q[0] for q in actual]
    assert [q["question_text"] for q in data["questions"]] == [q[1] for q in actual]
    after = snapshot()
    assert len(after["evaluations"]) == len(before["evaluations"]) + 1
    assert len(after["questions"]) == len(before["questions"]) + count
    for table in ("users", "courses", "course_enrollments"):
        assert after[table] == before[table]


@pytest.mark.parametrize("identity,expected", [(None, 401), (1, 403), (999, 401)])
def test_creation_denies_invalid_actor(api_client, identity, expected):
    if identity is not None:
        login(api_client, identity)  # A stale/forged role never overrides DB identity.
    before = snapshot()
    data = payload()
    data.update({"user_id": 2, "created_by": 2, "role": "lecturer"})
    assert api_client.post("/api/evaluations?user_id=2", json=data).status_code == expected
    assert snapshot() == before


def test_unassigned_creation_exact_message_and_no_writes(api_client):
    login(api_client, 2)
    with closing(sqlite3.connect(module.DATABASE)) as db, db:
        db.execute("INSERT INTO courses (id,course_code,course_name) VALUES (2,'OTHER202','Other Course')")
    before = snapshot()
    data = payload()
    data["course_id"] = 2  # Lecturer still owns course 1, but not this selected course.
    response = api_client.post("/api/evaluations", json=data)
    assert response.status_code == 403
    assert response.get_json()["error"]["message"] == "You do not have permission to create an evaluation for this course."
    assert snapshot() == before


def test_administrator_creation_reuses_us08_without_course_assignment(api_client):
    login(api_client, 3, "administrator")
    response = api_client.post("/api/evaluations", json=payload())
    assert response.status_code == 201
    with closing(sqlite3.connect(module.DATABASE)) as db:
        assert db.execute("SELECT created_by FROM evaluations WHERE id=?", (response.get_json()["evaluation_id"],)).fetchone() == (3,)
        assert db.execute("SELECT COUNT(*) FROM course_lecturers WHERE lecturer_id=3").fetchone()[0] == 0


@pytest.mark.parametrize("field,value,code", [
    ("title", "  ", "MISSING_TITLE"), ("deadline", None, "MISSING_DEADLINE"),
    ("deadline", "not-a-date", "INVALID_DEADLINE"), ("course_id", True, "INVALID_COURSE_ID"),
    ("course_id", 999, "COURSE_NOT_FOUND"), ("questions", None, "MISSING_QUESTIONS"),
    ("questions", [{"question_text": "ok", "question_type": "other"}], "INVALID_QUESTION_TYPE"),
    ("questions", [{"question_text": "ok", "question_type": "rating", "is_required": 1}], "INVALID_IS_REQUIRED"),
    ("questions", [True], "INVALID_QUESTION"),
    ("questions", [{"question_text": " ", "question_type": "rating"}], "INVALID_QUESTION_TEXT"),
], ids=["title", "missing-deadline", "bad-deadline", "bad-course", "missing-course", "missing-questions",
        "question-type", "required-type", "question-object", "question-text"])
def test_invalid_creation_has_no_writes(api_client, field, value, code):
    login(api_client, 2)
    data = payload()
    data[field] = value
    before = snapshot()
    response = api_client.post("/api/evaluations", json=data)
    assert response.status_code == (404 if code == "COURSE_NOT_FOUND" else 400)
    assert response.get_json()["error"]["code"] == code
    if code == "MISSING_DEADLINE":
        assert response.get_json()["error"]["message"] == "A deadline is required."
    assert snapshot() == before


def test_question_failure_rolls_back_evaluation_and_prior_question(api_client, monkeypatch):
    login(api_client, 2)
    original = module.get_db_connection
    reached = []

    def connect():
        db = original()
        db.create_function("record_failure", 0, lambda: reached.append(True) or 0)
        return db

    monkeypatch.setattr(module, "get_db_connection", connect)
    with closing(sqlite3.connect(module.DATABASE)) as db:
        db.execute("""CREATE TRIGGER fail_question BEFORE INSERT ON questions
            WHEN NEW.question_order=2 AND EXISTS (
              SELECT 1 FROM questions WHERE evaluation_id=NEW.evaluation_id AND question_order=1)
            BEGIN SELECT record_failure(); SELECT RAISE(ABORT, 'private write failure'); END""")
    before = snapshot()
    response = api_client.post("/api/evaluations", json=payload())
    assert reached == [True]
    assert response.status_code == 503 and response.get_json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "private write failure" not in response.text
    assert snapshot() == before
    with closing(sqlite3.connect(module.DATABASE)) as db:
        db.execute("DROP TRIGGER fail_question")
    assert api_client.post("/api/evaluations", json=payload()).status_code == 201
