"""Pre-submission P0 regressions, with temporary SQLite and controlled time."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

import pytest

from src import app as app_module


def student_session(client):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['role'] = 'student'


@pytest.fixture
def audit_client(api_client):
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("DELETE FROM response_answers")
        db.execute("DELETE FROM responses")
    student_session(api_client)
    return api_client


def test_team_taught_course_has_one_evaluation(audit_client):
    """M5-A01 / US02: team teaching cannot duplicate cards or inflate totals."""
    student_session(audit_client)
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("INSERT INTO users (id,email,password_hash,full_name,role) VALUES (9,'co@test.com','unused','Co Lecturer','lecturer')")
        db.execute('INSERT INTO course_lecturers (lecturer_id,course_id) VALUES (9,1)')
    result = audit_client.get('/api/evaluations').get_json()
    assert result['count'] == 1
    assert [row['id'] for row in result['evaluations']] == [1]
    questions = audit_client.get('/api/evaluations/1/questions').get_json()
    assert result['evaluations'][0]['lecturer_name'] == questions['evaluation']['lecturer_name']


@pytest.mark.parametrize('closed', [False, True], ids=['expired','closed'])
def test_saved_completion_survives_evaluation_closure(audit_client, closed):
    """M5-A02 / US03: a saved receipt stays available after the deadline/closure."""
    student_session(audit_client)
    payload = {'evaluation_id': 1, 'answers': {'1': {'rating_value': 5}, '2': {'text_value': 'Saved feedback.'}}}
    assert audit_client.post('/api/submissions', json=payload).status_code == 201
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("UPDATE evaluations SET deadline='2020-01-01', status=? WHERE id=1", ('closed' if closed else 'open',))
    result = audit_client.get('/api/evaluations/1/questions')
    assert result.status_code == 409
    assert result.get_json()['error']['code'] == 'DUPLICATE_SUBMISSION'
    assert audit_client.get('/api/evaluations').get_json()['evaluations'][0]['survey_status'] == 'Completed'
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute("SELECT COUNT(*) FROM responses WHERE status='submitted'").fetchone()[0] == 1


@pytest.mark.parametrize("draft", [False, True], ids=["new-response", "existing-draft"])
def test_simultaneous_submission_is_conflict_not_server_error(audit_client, monkeypatch, draft):
    """M5-A03 / US03: competing tabs save once and receive a canonical 409."""
    if draft:
        with sqlite3.connect(app_module.DATABASE) as db:
            response_id = db.execute("INSERT INTO responses (evaluation_id, student_id, status) VALUES (1,1,'draft')").lastrowid
            db.execute("INSERT INTO response_answers (response_id, question_id, rating_value) VALUES (?,1,2)", (response_id,))
    original = app_module.get_db_connection
    first_write = Event()
    second_write = Event()
    lock = Lock()
    writes = 0

    def connection():
        db = original()

        def trace(sql):
            nonlocal writes
            write_statement = 'DELETE FROM response_answers' if draft else 'INSERT INTO responses'
            if write_statement not in sql:
                return
            with lock:
                writes += 1
                ordinal = writes
            if ordinal == 1:
                # Hold just before persistence: without a write transaction the
                # other tab can pass its duplicate SELECT on a stale snapshot.
                first_write.set()
                second_write.wait(timeout=0.5)
            else:
                second_write.set()

        db.set_trace_callback(trace)
        return db

    monkeypatch.setattr(app_module, 'get_db_connection', connection)

    def submit(rating):
        with app_module.app.test_client() as client:
            student_session(client)
            result = client.post('/api/submissions', json={'evaluation_id': 1, 'answers': {'1': {'rating_value': rating}, '2': {'text_value': 'Concurrent feedback.'}}})
            return result.status_code, result.get_json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submit, 4)
        assert first_write.wait(timeout=5)
        second = pool.submit(submit, 5)
        results = [first.result(timeout=10), second.result(timeout=10)]
    assert sorted(status for status, _ in results) == [201, 409]
    assert next(body for status, body in results if status == 409)['error']['code'] == 'DUPLICATE_SUBMISSION'
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute("SELECT COUNT(*) FROM responses WHERE status='submitted'").fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM response_answers').fetchone()[0] == 2
