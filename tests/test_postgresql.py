"""Real PostgreSQL integration on disposable schemas, never a Neon runtime URL.

EDUSURVEY_TEST_POSTGRES_URL must name a dedicated local/CI database. Every case
uses a random new schema; only that schema is cleaned up. Without a test server,
new integration cases explicitly report BLOCKED, never fabricated success.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Thread
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import pytest
from flask import Flask
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from src import app as app_module
from src.database import bind_sql, connect
from src.pg_driver import psycopg
from src.runtime import configure_runtime

sql = psycopg.sql if psycopg else None
from tools.migrate_postgres import migrate
from tools.seed_postgres import copy_snapshot, seed_demo


@pytest.fixture
def pg_url():
    if psycopg is None:
        pytest.skip('BLOCKED: install requirements-postgres.txt')
    url = os.environ.get('EDUSURVEY_TEST_POSTGRES_URL')
    if not url:
        pytest.skip('BLOCKED: dedicated PostgreSQL test instance not configured')
    parsed = urlsplit(url)
    if parsed.hostname not in {'localhost', '127.0.0.1'} or not parsed.path.startswith('/edusurvey_test'):
        pytest.fail('Refusing integration tests outside a dedicated localhost edusurvey_test database')
    schema = 'test_' + uuid4().hex
    with psycopg.connect(url, autocommit=True) as db:
        db.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    query = dict(parse_qsl(parsed.query))
    query['options'] = '-csearch_path=' + schema
    isolated = urlunsplit(parsed._replace(query=urlencode(query)))
    try:
        yield isolated
    finally:
        with psycopg.connect(url, autocommit=True) as db:
            db.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.fixture
def pg_client(api_client, pg_url, monkeypatch):
    migrate(pg_url)
    copy_snapshot(Path(app_module.DATABASE), pg_url)
    with connect(pg_url) as db:
        db.execute('DELETE FROM response_answers')
        db.execute('DELETE FROM responses')
    monkeypatch.setattr(app_module, 'DATABASE', pg_url)
    return api_client


def login(client, role='student'):
    # api_client's original fixture deliberately uses a non-password hash.
    with client.session_transaction() as session:
        session['user_id'] = {'student': 1, 'lecturer': 2, 'administrator': 3}[role]
        session['role'] = role


def payload():
    return {'evaluation_id': 1, 'answers': {'1': {'rating_value': 5},
                                         '2': {'text_value': 'Useful course content.'}}}


def test_schema_idempotence_and_seed_refusal(pg_url):
    counts = seed_demo(pg_url)
    assert counts['users'] == 6 and counts['questions'] == 30
    migrate(pg_url)
    with pytest.raises(RuntimeError, match='nonempty'):
        seed_demo(pg_url)
    with connect(pg_url) as db:
        assert db.execute('SELECT COUNT(*) AS n FROM users').fetchone()['n'] == 6
        new = db.insert_id("INSERT INTO courses (course_code, course_name) VALUES (?, ?)", ('NEW', 'New'))
        assert new == 6


@pytest.mark.parametrize('statement', [
    "INSERT INTO users (email,password_hash,full_name,role) VALUES ('bad','h','Bad','invalid')",
    "INSERT INTO course_enrollments (student_id,course_id) VALUES (999,1)",
    "INSERT INTO course_enrollments (student_id,course_id) VALUES (1,1)",
    "INSERT INTO questions (evaluation_id,question_text,question_type,is_required,question_order) VALUES (1,'Q','rating',2,10)",
    "INSERT INTO responses (evaluation_id,student_id,status) VALUES (1,1,'invalid')",
    "INSERT INTO users (email,password_hash,full_name,role) VALUES (NULL,'h','Bad','student')",
])
def test_constraints_and_rollback(pg_client, pg_url, statement):
    with pytest.raises(psycopg.IntegrityError), connect(pg_url) as db:
        db.execute("UPDATE courses SET course_name='MUST ROLLBACK' WHERE id=1")
        db.execute(statement)
    with connect(pg_url) as db:
        assert db.execute('SELECT course_name FROM courses WHERE id=1').fetchone()['course_name'] != 'MUST ROLLBACK'


def test_submission_persistence_duplicate_feedback_logout(pg_client, pg_url):
    login(pg_client)
    assert pg_client.get('/api/evaluations').status_code == 200
    assert pg_client.get('/api/evaluations/1/questions').status_code == 200
    result = pg_client.post('/api/submissions', json=payload())
    assert result.status_code == 201, result.json
    assert pg_client.post('/api/submissions', json=payload()).status_code == 409
    with connect(pg_url) as db:
        assert db.execute("SELECT COUNT(*) AS n FROM responses WHERE status='submitted' AND student_id=1").fetchone()['n'] == 1
        assert db.execute('SELECT COUNT(*) AS n FROM response_answers').fetchone()['n'] >= 2
    login(pg_client, 'lecturer')
    assert pg_client.get('/lecturer/feedback/1').status_code == 200
    assert pg_client.get('/api/evaluations/1/statistics').status_code == 200
    assert pg_client.get('/api/evaluations').status_code == 403
    assert pg_client.post('/api/auth/logout').status_code == 200
    assert pg_client.post('/api/auth/logout').status_code == 200
    assert pg_client.get('/api/evaluations').status_code == 401


@pytest.mark.parametrize('deadline,expected', [('2026-11-04 11:59:59', 400), ('2026-11-04 12:00:00', 400), ('2026-11-04 12:00:01', 201), ('2026-11-04T19:00:01+07:00', 201)])
def test_deadline_boundaries(pg_client, pg_url, deadline, expected):
    with connect(pg_url) as db:
        db.execute('UPDATE evaluations SET deadline=? WHERE id=1', (deadline,))
    login(pg_client)
    result = pg_client.post('/api/submissions', json=payload())
    assert result.status_code == expected, result.json


def test_concurrent_submissions(pg_client, pg_url):
    gate = Barrier(2)
    def submit(_):
        with app_module.app.test_client() as client:
            login(client)
            gate.wait(timeout=5)
            return client.post('/api/submissions', json=payload()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, range(2))) == [201, 409]


def test_health_and_sanitized_failure(pg_client, pg_url, monkeypatch):
    assert pg_client.get('/health').json == {'status': 'ok', 'database': 'ok'}
    monkeypatch.setattr(app_module, 'DATABASE', 'postgresql://127.0.0.1:1/edusurvey_test?connect_timeout=1')
    assert pg_client.get('/health').status_code == 503
    login(pg_client)
    result = pg_client.get('/api/evaluations')
    assert result.status_code == 503 and result.json['error']['code'] == 'DATABASE_UNAVAILABLE'
    assert 'postgresql' not in result.text


@pytest.mark.parametrize('url', [None, 'sqlite:///local.db', 'postgresql://localhost/db?sslmode=disable'])
def test_render_requires_ssl_database_url(monkeypatch, url):
    monkeypatch.setenv('EDUSURVEY_ENV', 'production')
    monkeypatch.setenv('EDUSURVEY_SECRET_KEY', 'synthetic-secret-' * 4)
    monkeypatch.setenv('EDUSURVEY_DATABASE_BACKEND', 'postgresql')
    monkeypatch.setenv('EDUSURVEY_DATABASE', '/tmp/should-not-be-created.db')
    monkeypatch.delenv('DATABASE_URL', raising=False)
    if url:
        monkeypatch.setenv('DATABASE_URL', url)
    with pytest.raises(RuntimeError):
        configure_runtime(Flask(__name__), 'unused.db')


def test_binding_keeps_literals_and_comments():
    statement = "SELECT '?' AS literal, :value AS n, ?::text -- ? :name\n"
    assert bind_sql(statement, {}) == "SELECT '?' AS literal, %(value)s AS n, %s::text -- ? :name\n"


@pytest.mark.parametrize('width', [1440, 390], ids=['laptop', 'phone'])
def test_postgres_browser_p0(pg_url, monkeypatch, width):
    seed_demo(pg_url)
    monkeypatch.setattr(app_module, 'DATABASE', pg_url)
    monkeypatch.setitem(app_module.app.config, 'TESTING', True)
    server = make_server('127.0.0.1', 0, app_module.app, threaded=True)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if path := os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
                options['executable_path'] = path
            browser = playwright.chromium.launch(**options)
            try:
                page = browser.new_page(viewport={'width': width, 'height': 900 if width > 600 else 844})
                page.goto(origin)
                page.get_by_label('Email', exact=False).fill('student1@edusurvey.edu')
                page.locator('#password').fill('Password123!')
                page.get_by_role('button', name='Sign in', exact=True).click()
                expect(page).to_have_url(origin + '/evaluations')
                page.goto(origin + '/evaluations/1/complete')
                ratings = page.locator('input[type="radio"][value="5"]')
                expect(ratings).to_have_count(2)
                for rating in ratings.all():
                    rating.focus()
                    page.keyboard.press('Space')
                page.locator('textarea').fill('Useful course content.')
                page.locator('#reviewButtonMobile' if width < 600 else '#reviewButton').click()
                page.get_by_role('button', name='Submit evaluation', exact=True).click()
                expect(page.locator('#submissionSuccess')).to_be_visible()
                page.reload()
                expect(page.locator('#submissionSuccess')).to_be_visible()
                page.get_by_role('button', name='Sign out', exact=True).click()
                expect(page).to_have_url(origin + '/login')
                page.get_by_label('Email', exact=False).fill('lecturer1@edusurvey.edu')
                page.locator('#password').fill('Password123!')
                page.get_by_role('button', name='Sign in', exact=True).click()
                expect(page).to_have_url(origin + '/lecturer/feedback')
                page.goto(origin + '/lecturer/feedback/1')
                expect(page.get_by_text('Useful course content.', exact=True).first).to_be_visible()
                assert page.request.get(origin + '/api/evaluations').status == 403
            finally:
                browser.close()
    finally:
        server.shutdown()
        worker.join(timeout=5)
        server.server_close()


def test_read_api_contract_parity(api_client, pg_url, monkeypatch):
    """Exact JSON/status parity, including text dates, counts and numeric AVG."""
    sqlite_path = app_module.DATABASE
    migrate(pg_url)
    copy_snapshot(Path(sqlite_path), pg_url)
    for role, paths in [
        ('student', ['/api/auth/me', '/api/evaluations', '/api/evaluations/1/questions']),
        ('lecturer', ['/api/auth/me', '/api/courses/1/feedback',
                      '/api/evaluations/1/feedback/topics', '/api/evaluations/1/statistics']),
    ]:
        for path in paths:
            monkeypatch.setattr(app_module, 'DATABASE', sqlite_path)
            login(api_client, role)
            old = api_client.get(path)
            monkeypatch.setattr(app_module, 'DATABASE', pg_url)
            login(api_client, role)
            new = api_client.get(path)
            assert (new.status_code, new.json) == (old.status_code, old.json), path


@pytest.mark.parametrize('hours,status', [(23.999, 'Due soon'), (24, 'Active'), (24.001, 'Active')])
def test_due_soon_boundary(pg_client, pg_url, fixed_app_clock, hours, status):
    from datetime import timedelta
    deadline = (fixed_app_clock + timedelta(hours=hours)).isoformat()
    with connect(pg_url) as db:
        db.execute('UPDATE evaluations SET deadline=? WHERE id=1', (deadline,))
    login(pg_client)
    assert pg_client.get('/api/evaluations').json['evaluations'][0]['survey_status'] == status


def test_submission_partial_write_rolls_back(pg_client, pg_url):
    with connect(pg_url) as db:
        db.raw.execute("""
            CREATE FUNCTION reject_second_answer() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF NEW.question_id = 2 THEN RAISE EXCEPTION 'synthetic failure'; END IF;
            RETURN NEW; END $$;
            CREATE TRIGGER fail_answer BEFORE INSERT ON response_answers
            FOR EACH ROW EXECUTE FUNCTION reject_second_answer();
        """)
    login(pg_client)
    assert pg_client.post('/api/submissions', json=payload()).status_code == 503
    with connect(pg_url) as db:
        assert db.execute('SELECT COUNT(*) AS n FROM responses').fetchone()['n'] == 0
        assert db.execute('SELECT COUNT(*) AS n FROM response_answers').fetchone()['n'] == 0
        db.execute('DROP TRIGGER fail_answer ON response_answers')
    assert pg_client.post('/api/submissions', json=payload()).status_code == 201


def test_role_changes_and_deleted_accounts(pg_client, pg_url):
    login(pg_client, 'lecturer')
    with connect(pg_url) as db:
        db.execute("UPDATE users SET role='student' WHERE id=2")
    assert pg_client.get('/api/evaluations/1/statistics').status_code == 403
    login(pg_client)
    with connect(pg_url) as db:
        db.execute('DELETE FROM response_answers')
        db.execute('DELETE FROM evaluations')
        db.execute('DELETE FROM users WHERE id=1')
    assert pg_client.get('/api/evaluations').status_code == 401


def test_reminder_and_expiry_sql(pg_client, pg_url, fixed_app_clock):
    from datetime import timedelta
    with connect(pg_url) as db:
        db.execute("UPDATE evaluations SET deadline=? WHERE id=1", ((fixed_app_clock + timedelta(hours=24)).isoformat(),))
        db.execute("INSERT INTO responses (evaluation_id,student_id,status) VALUES (1,1,'draft')")
    assert len(app_module.send_deadline_reminders(now=fixed_app_clock)) == 1
    assert app_module.send_deadline_reminders(now=fixed_app_clock) == []
    with connect(pg_url) as db:
        db.execute("UPDATE evaluations SET deadline='2000-01-01T00:00:00+07:00' WHERE id=1")
        app_module.close_expired_evaluations(db)
        assert db.execute('SELECT status FROM evaluations WHERE id=1').fetchone()['status'] == 'closed'


def test_named_query_files(pg_client, pg_url):
    root = Path(__file__).resolve().parents[1]
    with connect(pg_url) as db:
        for file in ['response_queries.sql', 'feedback_queries.sql']:
            source = (root / 'src' / file).read_text()
            source = '\n'.join(line for line in source.splitlines() if not line.lstrip().startswith('--'))
            statements = source.split(';')
            for statement in statements:
                if not statement.strip():
                    continue
                # EXPLAIN validates bind conversion/types/SQL without changing data.
                db.execute('EXPLAIN ' + statement, {'evaluation_id': 1, 'student_id': 1,
                           'response_id': -1, 'question_id': 1, 'rating_value': 5,
                           'text_value': 'Synthetic', 'course_id': 1, 'lecturer_id': 2}).fetchall()


def test_unknown_schema_is_not_modified(pg_url):
    with connect(pg_url) as db:
        db.execute('CREATE TABLE unrelated (id INTEGER PRIMARY KEY)')
        db.execute('INSERT INTO unrelated VALUES (7)')
    with pytest.raises(RuntimeError, match='nonempty'):
        migrate(pg_url)
    with connect(pg_url) as db:
        assert db.execute('SELECT id FROM unrelated').fetchone()['id'] == 7


@pytest.mark.parametrize('evaluation_id', [2147483648, 9223372036854775807, 9223372036854775808])
def test_large_missing_ids_keep_api_contract(pg_client, evaluation_id):
    login(pg_client)
    data = payload()
    data['evaluation_id'] = evaluation_id
    result = pg_client.post('/api/submissions', json=data)
    assert result.status_code == 404, result.json


@pytest.mark.parametrize('draft', [False, True])
def test_concurrent_draft_and_new_submissions(pg_client, pg_url, draft):
    if draft:
        with connect(pg_url) as db:
            response = db.insert_id("INSERT INTO responses (evaluation_id,student_id,status) VALUES (1,1,'draft')", ())
            db.execute('INSERT INTO response_answers (response_id,question_id,rating_value) VALUES (?,1,2)', (response,))
    test_concurrent_submissions(pg_client, pg_url)
    with connect(pg_url) as db:
        assert db.execute('SELECT COUNT(*) AS n FROM response_answers').fetchone()['n'] == 2


def test_startup_verifies_without_reseeding(pg_url, monkeypatch):
    from tools.prepare_production import prepare_database
    monkeypatch.setenv('EDUSURVEY_ENV', 'production')
    monkeypatch.setenv('EDUSURVEY_SECRET_KEY', 'synthetic-key-' * 4)
    # localhost test server has no TLS; exercise readiness independently of the
    # production SSL validator, which is covered by its own configuration tests.
    import tools.prepare_production as preparation
    monkeypatch.setattr(preparation, 'configure_runtime', lambda *args: pg_url)
    with pytest.raises(RuntimeError, match='schema missing'):
        prepare_database()
    seed_demo(pg_url)
    with connect(pg_url) as db:
        db.execute("UPDATE courses SET course_name='Persistent marker' WHERE id=1")
    prepare_database()
    prepare_database()
    with connect(pg_url) as db:
        assert db.execute('SELECT course_name FROM courses WHERE id=1').fetchone()['course_name'] == 'Persistent marker'


def test_actual_credentials_on_postgres(pg_url, monkeypatch):
    seed_demo(pg_url)
    monkeypatch.setattr(app_module, 'DATABASE', pg_url)
    with app_module.app.test_client() as client:
        assert client.post('/api/auth/login', json={'email': 'student1@edusurvey.edu', 'password': 'incorrect'}).status_code == 401
        result = client.post('/api/auth/login', json={'email': 'student1@edusurvey.edu', 'password': 'Password123!'})
        assert result.status_code == 200
        assert client.get('/api/auth/me').json['user']['role'] == 'student'


def test_schema_checksum_mismatch_refused(pg_url):
    migrate(pg_url)
    with connect(pg_url) as db:
        db.execute("UPDATE edusurvey_migrations SET checksum='invalid'")
    with pytest.raises(RuntimeError, match='checksum'):
        migrate(pg_url)
