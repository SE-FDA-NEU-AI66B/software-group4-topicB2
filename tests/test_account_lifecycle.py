"""Isolated SQLite lifecycle/security contracts; no production configuration."""
import hashlib
import sqlite3
from urllib.parse import parse_qs, urlsplit

import pytest

from src import app as app_module
from src.account_store import migrate_accounts


@pytest.fixture
def accounts(api_client):
    migrate_accounts(app_module.DATABASE)
    with api_client.session_transaction() as session:
        session['user_id'], session['role'] = 3, 'administrator'
    return api_client


def provision(client, email='new@example.edu', role='student'):
    return client.post('/api/admin/accounts', json={'name': 'New University User', 'email': email, 'role': role})


def token(result):
    return parse_qs(urlsplit(result['setup_path']).fragment)['token'][0]


def redeem(client, secret):
    return client.post('/api/auth/set-password', json={'token': secret, 'password': 'New-unique-passphrase-123'})


def login_admin(client):
    with client.session_transaction() as session:
        session.clear()
        session['user_id'], session['role'] = 3, 'administrator'


def test_migration_is_additive_idempotent(api_client):
    with sqlite3.connect(app_module.DATABASE) as db:
        before = {table: db.execute(f'SELECT * FROM {table} ORDER BY id').fetchall() for table in ('users', 'responses', 'response_answers')}
    migrate_accounts(app_module.DATABASE)
    migrate_accounts(app_module.DATABASE)
    with sqlite3.connect(app_module.DATABASE) as db:
        for table, records in before.items():
            assert db.execute(f'SELECT * FROM {table} ORDER BY id').fetchall() == records
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_invitation_password_and_replay(accounts, caplog):
    created = provision(accounts)
    assert created.status_code == 201
    result = created.json['account']
    secret = token(result)
    with sqlite3.connect(app_module.DATABASE) as db:
        row = db.execute('SELECT digest FROM account_tokens').fetchone()
        assert row[0] == hashlib.sha256(secret.encode()).hexdigest()
        assert secret not in repr(db.execute('SELECT * FROM account_tokens').fetchall())
    assert accounts.post('/api/auth/login', json={'email': result['email'], 'password': 'anything'}).status_code == 401
    assert redeem(accounts, secret).status_code == 200
    assert redeem(accounts, secret).status_code == 400
    assert accounts.post('/api/auth/login', json={'email': result['email'], 'password': 'New-unique-passphrase-123'}).status_code == 200
    assert accounts.get('/api/auth/me').json['user']['role'] == 'student'
    assert accounts.post('/api/admin/accounts', json={}).status_code == 403
    assert secret not in caplog.text and 'New-unique-passphrase-123' not in caplog.text
    assert accounts.get('/activate').headers['referrer-policy'] == 'no-referrer'
    assert accounts.get('/activate').headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('role', ['administrator', 'invalid', '', None])
def test_no_privileged_provisioning(accounts, role):
    assert provision(accounts, role=role).status_code == 400
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 3


def test_unauthorized_and_cross_origin(accounts):
    accounts.post('/api/auth/logout')
    assert provision(accounts).status_code == 401
    assert accounts.get('/admin/accounts').status_code == 302
    with accounts.session_transaction() as session:
        session['user_id'], session['role'] = 2, 'lecturer'
    assert provision(accounts).status_code == 403
    login_admin(accounts)
    assert accounts.post('/api/admin/accounts', json={'name': 'New', 'email': 'x@example.edu', 'role': 'student'}, headers={'Origin': 'https://attacker.test'}).status_code == 403
    assert provision(accounts, email=' Student@Test.Com ').status_code == 409


def test_expiry_reissue_and_disabled_tokens(accounts):
    created = provision(accounts).json['account']
    first = token(created)
    second = token(accounts.post(f"/api/admin/accounts/{created['id']}/invitation", json={}).json)
    assert redeem(accounts, first).status_code == 400
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute('UPDATE account_tokens SET expires_at=? WHERE digest=?', ('2000-01-01T00:00:00+00:00', hashlib.sha256(second.encode()).hexdigest()))
    assert redeem(accounts, second).status_code == 400
    current = token(accounts.post(f"/api/admin/accounts/{created['id']}/invitation", json={}).json)
    assert accounts.patch(f"/api/admin/accounts/{created['id']}/state", json={'state': 'disabled'}).status_code == 200
    assert redeem(accounts, current).status_code == 400
    assert accounts.patch(f"/api/admin/accounts/{created['id']}/state", json={'state': 'active'}).json['state'] == 'invited'


def test_disable_reactivate_and_reset_revoke_existing_sessions(accounts):
    result = provision(accounts).json['account']
    assert redeem(accounts, token(result)).status_code == 200
    assert accounts.post('/api/auth/login', json={'email': result['email'], 'password': 'New-unique-passphrase-123'}).status_code == 200
    cookie = accounts.get_cookie('session').value
    admin = app_module.app.test_client()
    login_admin(admin)
    assert admin.patch(f"/api/admin/accounts/{result['id']}/state", json={'state': 'disabled'}).status_code == 200
    assert accounts.get('/api/auth/me').status_code == 401
    assert accounts.post('/api/auth/login', json={'email': result['email'], 'password': 'New-unique-passphrase-123'}).status_code == 401
    assert admin.patch(f"/api/admin/accounts/{result['id']}/state", json={'state': 'active'}).status_code == 200
    accounts.set_cookie('session', cookie)
    assert accounts.get('/api/auth/me').status_code == 401
    assert accounts.post('/api/auth/login', json={'email': result['email'], 'password': 'New-unique-passphrase-123'}).status_code == 200
    reset = admin.post(f"/api/admin/accounts/{result['id']}/invitation", json={}).json
    assert redeem(admin, token(reset)).status_code == 200
    assert accounts.get('/api/auth/me').status_code == 401


def test_last_active_admin_protected_everywhere(accounts):
    assert accounts.patch('/api/admin/accounts/3/state', json={'state': 'disabled'}).status_code == 409
    assert accounts.post('/api/admin/accounts/3/invitation', json={}).status_code == 409
    assert accounts.patch('/api/admin/users/3/role', json={'role': 'student'}).status_code == 409
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("INSERT INTO users(id,email,full_name,role,password_hash) VALUES(4,'second@example.edu','Second Admin','administrator','h')")
    assert accounts.patch('/api/admin/accounts/4/state', json={'state': 'disabled'}).status_code == 200
    assert accounts.patch('/api/admin/users/3/role', json={'role': 'student'}).status_code == 409


def test_csv_preview_confirm_replay_and_changed_input(accounts):
    source = 'name,email,role\nNew Student,import@example.edu,student\nNew Lecturer,lecturer@example.edu,lecturer\n'
    preview = accounts.post('/api/admin/accounts/import-preview', json={'csv': source})
    assert preview.status_code == 200 and preview.json['valid']
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 3
    request = {'csv': source, 'confirmation': preview.json['confirmation']}
    assert accounts.post('/api/admin/accounts/import-confirm', json=request | {'csv': source.replace('New Student', 'Changed Name')}).status_code == 409
    confirmed = accounts.post('/api/admin/accounts/import-confirm', json=request)
    assert confirmed.status_code == 201 and len(confirmed.json['accounts']) == 2
    assert accounts.post('/api/admin/accounts/import-confirm', json=request).status_code == 409
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 5


@pytest.mark.parametrize('source', ['name,email,role\nA,a@example.edu,student\nB,A@EXAMPLE.EDU,lecturer', 'name,email,role\nA,student@test.com,student', 'name,email,role\nA,invalid,student', 'name,email,role\nA,a@example.edu,administrator'])
def test_csv_errors_never_create_accounts(accounts, source):
    preview = accounts.post('/api/admin/accounts/import-preview', json={'csv': source})
    assert preview.status_code == 200
    assert preview.json['valid'] is False and preview.json['confirmation'] is None
    assert any(row['error'] for row in preview.json['rows'])


def test_csv_ticket_is_actor_bound_and_expiring(accounts, monkeypatch):
    import itsdangerous.timed
    source = 'name,email,role\nA,a@example.edu,student'
    from itsdangerous import URLSafeTimedSerializer
    signer = URLSafeTimedSerializer(app_module.app.secret_key, salt='edusurvey-account-import')
    payload = signer.loads(accounts.post('/api/admin/accounts/import-preview', json={'csv': source}).json['confirmation'])
    with monkeypatch.context() as patch:
        patch.setattr(itsdangerous.timed.TimestampSigner, 'get_timestamp', lambda _self: 1000)
        expired = signer.dumps(payload)
    assert accounts.post('/api/admin/accounts/import-confirm', json={'csv': source, 'confirmation': expired}).status_code == 400
    ticket = accounts.post('/api/admin/accounts/import-preview', json={'csv': source}).json['confirmation']
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("INSERT INTO users(id,email,full_name,role,password_hash) VALUES(4,'second@example.edu','Second','administrator','h')")
    with accounts.session_transaction() as session:
        session['user_id'], session['role'] = 4, 'administrator'
    assert accounts.post('/api/admin/accounts/import-confirm', json={'csv': source, 'confirmation': ticket}).status_code == 403


def test_membership_transfer_is_atomic_and_preserves_feedback(accounts):
    new = provision(accounts, email='other@example.edu', role='lecturer').json['account']
    assert accounts.post('/api/admin/memberships', json={'action': 'remove', 'user_id': 2, 'course_id': 1}).status_code == 409
    assert accounts.post('/api/admin/memberships', json={'action': 'transfer', 'user_id': 2, 'target_id': 1, 'course_id': 1}).status_code == 400
    assert accounts.post('/api/admin/memberships', json={'action': 'transfer', 'user_id': 2, 'target_id': new['id'], 'course_id': 1}).status_code == 200
    assert accounts.post('/api/admin/memberships', json={'action': 'remove', 'user_id': 1, 'course_id': 1}).status_code == 200
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM responses').fetchone()[0] == 1
        assert db.execute('SELECT student_id FROM responses').fetchone()[0] == 1
        assert db.execute('SELECT lecturer_id FROM course_lecturers').fetchone()[0] == new['id']
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_lifecycle_checks_legacy_mutation_routes(accounts):
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("INSERT INTO account_access(user_id,state,version,updated_at) VALUES(2,'disabled',1,'now')")
    with accounts.session_transaction() as session:
        session['user_id'], session['role'] = 2, 'lecturer'
    assert accounts.post('/api/evaluations', json={}).status_code == 401
    with accounts.session_transaction() as session:
        session['user_id'], session['role'] = 2, 'lecturer'
    assert accounts.get('/api/evaluations/1/statistics').status_code == 401


def test_bulk_failure_rolls_back_users_tokens_and_confirmation(accounts):
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("CREATE TRIGGER reject_import BEFORE INSERT ON users WHEN NEW.email='blocked@example.edu' BEGIN SELECT RAISE(ABORT,'Synthetic import rejection'); END")
    source = 'name,email,role\nGood,good@example.edu,student\nBlocked,blocked@example.edu,student'
    ticket = accounts.post('/api/admin/accounts/import-preview', json={'csv': source}).json['confirmation']
    assert accounts.post('/api/admin/accounts/import-confirm', json={'csv': source, 'confirmation': ticket}).status_code == 503
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 3
        assert db.execute('SELECT COUNT(*) FROM account_tokens').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM account_imports').fetchone()[0] == 0


def test_concurrent_admin_disable_keeps_an_active_admin(accounts):
    from concurrent.futures import ThreadPoolExecutor
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("INSERT INTO users(id,email,full_name,role,password_hash) VALUES(4,'second@example.edu','Second Admin','administrator','fixture-hash')")
    def disable(actor):
        with app_module.app.test_client() as client:
            with client.session_transaction() as session:
                session['user_id'], session['role'] = actor, 'administrator'
            return client.patch(f'/api/admin/accounts/{7 - actor}/state', json={'state': 'disabled'}).status_code
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(disable, (3, 4)))
    assert results.count(200) == 1
    assert all(result in {200, 401, 403, 409} for result in results)
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute("SELECT COUNT(*) FROM users u LEFT JOIN account_access a ON a.user_id=u.id WHERE role='administrator' AND (a.state IS NULL OR a.state='active')").fetchone()[0] == 1
