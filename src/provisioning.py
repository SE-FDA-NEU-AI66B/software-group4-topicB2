"""Admin-managed account provisioning. No public registration or password delivery."""
import csv
import hashlib
import io
import json
import re
import secrets
from datetime import UTC, datetime, timedelta

from flask import jsonify, render_template, request, session
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

if __package__:
    from .account_store import access, active_admins, lock_admin, now_text, ready
    from .database import insert_id
else:
    from account_store import access, active_admins, lock_admin, now_text, ready
    from database import insert_id

EMAIL = re.compile(r'^[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+$')


def normalize(data):
    if not isinstance(data, dict):
        raise TypeError('Provide name, email and role.')
    name, email, role = data.get('name'), data.get('email'), data.get('role')
    if not isinstance(name, str) or not name.strip() or not name.strip().isprintable() or len(name.strip()) > 120:
        raise ValueError('Name must contain 1–120 characters.')
    if not isinstance(email, str) or len(email.strip()) > 254 or not email.strip().isascii() or any(ord(char) < 32 or ord(char) == 127 for char in email.strip()) or not EMAIL.fullmatch(email.strip()):
        raise ValueError('Enter a valid email address.')
    if role not in ('student', 'lecturer'):
        raise ValueError('Provisioning supports Student and Lecturer roles only.')
    return {'name': name.strip(), 'email': email.strip().lower(), 'role': role}


def issue_token(db, user_id, purpose):
    instant = datetime.now(UTC)
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()
    expires = (instant + timedelta(hours=24 if purpose == 'invite' else 1)).isoformat()
    db.execute('UPDATE account_tokens SET consumed_at=? WHERE user_id=? AND consumed_at IS NULL', (instant.isoformat(), user_id))
    db.execute('INSERT INTO account_tokens(digest,user_id,purpose,expires_at) VALUES (?,?,?,?)', (digest, user_id, purpose, expires))
    # Fragment is never included in HTTP access logs or Referer URLs.
    return {'setup_path': '/activate#token=' + token, 'expires_at': expires,
            'delivery': 'Private handoff required. No email has been sent.'}


def create_account(db, row):
    if db.execute('SELECT 1 FROM users WHERE lower(email)=?', (row['email'],)).fetchone():
        raise ValueError('An account with this email already exists.')
    user_id = insert_id(db, 'INSERT INTO users(email,full_name,role,password_hash) VALUES (?,?,?,?)',
                        (row['email'], row['name'], row['role'], '!password-not-set'))
    db.execute("INSERT INTO account_access(user_id,state,version,resume_state,updated_at) VALUES (?,'invited',0,'invited',?)", (user_id, now_text()))
    return dict(id=user_id, **row, **issue_token(db, user_id, 'invite'))


def parse_import(db, source):
    if not isinstance(source, str) or len(source.encode()) > 65536:
        raise ValueError('CSV must be text up to 64 KB.')
    reader = csv.DictReader(io.StringIO(source.lstrip('\ufeff')), strict=True)
    if reader.fieldnames != ['name', 'email', 'role']:
        raise ValueError('CSV header must be exactly: name,email,role')
    rows, seen = [], set()
    for line, raw in enumerate(reader, 2):
        if len(rows) >= 200:
            raise ValueError('Import at most 200 accounts per batch.')
        try:
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError('Every row must contain exactly three fields.')
            row = normalize(raw)
            if row['email'] in seen:
                raise ValueError('Duplicate email in this CSV.')
            if db.execute('SELECT 1 FROM users WHERE lower(email)=?', (row['email'],)).fetchone():
                raise ValueError('Email already exists.')
            seen.add(row['email'])
            rows.append({'line': line, **row, 'error': None})
        except ValueError as error:
            rows.append({'line': line, 'name': str(raw.get('name') or '')[:120], 'email': str(raw.get('email') or '')[:254], 'role': str(raw.get('role') or '')[:30], 'error': str(error)})
    if not rows:
        raise ValueError('CSV contains no accounts.')
    return rows


def register_provisioning(app, get_db, login_required, api_error):
    def fail(message, status=400):
        return api_error(status, 'ACCOUNT_REQUEST_REJECTED', message, 'Review the request and try again.')

    def authorize(db):
        if not ready(db):
            return fail('Account management is not enabled. An operator must apply the reviewed account migration.', 503)
        lock_admin(db)
        actor = db.execute('SELECT role FROM users WHERE id=?', (session['user_id'],)).fetchone()
        if actor is None or actor['role'] != 'administrator' or access(db, session['user_id'])['state'] != 'active':
            return fail('Administrator access is required.', 403)
        return None

    @app.before_request
    def check_lifecycle_origin():
        if (request.path.startswith('/api/admin/accounts') or request.path == '/api/admin/memberships') and request.method != 'GET' and request.headers.get('Origin') and request.headers['Origin'] not in {request.host_url.rstrip('/'), 'https://' + request.host}:
            return fail('Cross-origin administration requests are not allowed.', 403)
        return None

    @app.after_request
    def protect_account_responses(response):
        if request.path.startswith('/api/admin/accounts') or request.path in {'/activate', '/api/auth/set-password', '/admin/accounts'}:
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'no-referrer'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        if request.path == '/activate':
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.get('/admin/accounts')
    @login_required(roles=['administrator'])
    def account_management():
        return render_template('accounts.html')

    @app.get('/api/admin/accounts')
    @login_required(roles=['administrator'])
    def directory():
        with get_db() as db:
            if not ready(db):
                return fail('Account management requires the reviewed account migration.', 503)
            users = []
            for row in db.execute('''SELECT u.id,u.email,u.full_name,u.role,COALESCE(a.state,'active') AS state,
                (SELECT MAX(t.expires_at) FROM account_tokens t WHERE t.user_id=u.id AND t.consumed_at IS NULL) AS token_expires_at
                FROM users u LEFT JOIN account_access a ON a.user_id=u.id ORDER BY u.full_name,u.id''').fetchall():
                item = dict(row)
                item['invitation_status'] = 'Disabled' if item['state'] == 'disabled' else ('Setup pending' if item['token_expires_at'] and item['token_expires_at'] > now_text() else 'Invitation expired') if item['state'] == 'invited' else ('Password reset pending' if item['token_expires_at'] and item['token_expires_at'] > now_text() else 'Active')
                users.append(item)
            memberships = [dict(row) for row in db.execute("SELECT ce.student_id AS user_id,ce.course_id,c.course_name,'student' AS role FROM course_enrollments ce JOIN courses c ON c.id=ce.course_id UNION ALL SELECT cl.lecturer_id,cl.course_id,c.course_name,'lecturer' FROM course_lecturers cl JOIN courses c ON c.id=cl.course_id").fetchall()]
        return jsonify(users=users, memberships=memberships)

    @app.post('/api/admin/accounts')
    @login_required(roles=['administrator'])
    def provision():
        try:
            row = normalize(request.get_json(silent=True))
            with get_db() as db:
                if error := authorize(db):
                    return error
                if db.execute('SELECT 1 FROM users WHERE lower(email)=?', (row['email'],)).fetchone():
                    return fail('An account with this email already exists.', 409)
                result = create_account(db, row)
            return jsonify(account=result), 201
        except (ValueError, TypeError) as error:
            return fail(str(error))

    def protect_last_admin(db, user):
        return user['role'] == 'administrator' and access(db, user['id'])['state'] == 'active' and active_admins(db) <= 1

    @app.patch('/api/admin/accounts/<int:user_id>/state')
    @login_required(roles=['administrator'])
    def change_state(user_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or data.get('state') not in ('active', 'disabled'):
            return fail('Choose active or disabled.')
        with get_db() as db:
            if error := authorize(db):
                return error
            user = db.execute('SELECT id,role FROM users WHERE id=?', (user_id,)).fetchone()
            if user is None:
                return fail('Account not found.', 404)
            if protect_last_admin(db, user):
                return fail('The last active administrator cannot be modified.', 409)
            previous = db.execute('SELECT state,resume_state FROM account_access WHERE user_id=?', (user_id,)).fetchone()
            old_state = previous['state'] if previous else 'active'
            new_state = 'disabled' if data['state'] == 'disabled' else previous['resume_state'] if previous and old_state == 'disabled' else old_state
            resume = old_state if old_state != 'disabled' else previous['resume_state']
            db.execute('''INSERT INTO account_access(user_id,state,version,resume_state,updated_at) VALUES (?,?,1,?,?)
                ON CONFLICT(user_id) DO UPDATE SET state=excluded.state,version=account_access.version+1,resume_state=excluded.resume_state,updated_at=excluded.updated_at''', (user_id, new_state, resume, now_text()))
            db.execute('UPDATE account_tokens SET consumed_at=? WHERE user_id=? AND consumed_at IS NULL', (now_text(), user_id))
        if user_id == session['user_id']:
            session.clear()
        return jsonify(user_id=user_id, state=new_state)

    @app.post('/api/admin/accounts/<int:user_id>/invitation')
    @login_required(roles=['administrator'])
    def invitation(user_id):
        with get_db() as db:
            if error := authorize(db):
                return error
            user = db.execute('SELECT id,role FROM users WHERE id=?', (user_id,)).fetchone()
            if user is None:
                return fail('Account not found.', 404)
            state = access(db, user_id)['state']
            if state == 'disabled' or protect_last_admin(db, user):
                return fail('Disabled accounts and the last active administrator cannot receive reset links.', 409)
            result = issue_token(db, user_id, 'invite' if state == 'invited' else 'reset')
        return jsonify(**result)

    @app.get('/activate')
    def password_setup_page():
        return render_template('activate.html')

    @app.post('/api/auth/set-password')
    def set_password():
        data = request.get_json(silent=True)
        token = data.get('token') if isinstance(data, dict) else None
        credential = data.get('password') if isinstance(data, dict) else None
        if not isinstance(token, str) or not 40 <= len(token) <= 128:
            return fail('This setup link is invalid or expired.')
        if not isinstance(credential, str) or not 12 <= len(credential) <= 128 or not credential.strip():
            return fail('Use a password between 12 and 128 characters.')
        with get_db() as db:
            if not ready(db):
                return fail('Password setup is not available.', 503)
            lock_admin(db)
            row = db.execute('SELECT user_id,expires_at,consumed_at FROM account_tokens WHERE digest=?', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            if row is None or row['consumed_at'] is not None or row['expires_at'] <= now_text() or access(db, row['user_id'])['state'] == 'disabled':
                return fail('This setup link is invalid or expired.')
            owner = db.execute('SELECT id,role FROM users WHERE id=?', (row['user_id'],)).fetchone()
            if owner is None or protect_last_admin(db, owner):
                return fail('The last active administrator cannot be modified.', 409)
            try:
                credential.encode('utf-8')
            except UnicodeError:
                return fail('Password contains unsupported characters.')
            hashed = generate_password_hash(credential)
            db.execute('UPDATE users SET password_hash=? WHERE id=?', (hashed, row['user_id']))
            db.execute('''INSERT INTO account_access(user_id,state,version,resume_state,updated_at) VALUES (?,'active',1,'active',?)
                ON CONFLICT(user_id) DO UPDATE SET state='active',version=account_access.version+1,resume_state='active',updated_at=excluded.updated_at''', (row['user_id'], now_text()))
            db.execute('UPDATE account_tokens SET consumed_at=? WHERE user_id=? AND consumed_at IS NULL', (now_text(), row['user_id']))
        session.clear()
        return jsonify(message='Your password has been set. Sign in with your university email.')

    def serializer():
        return URLSafeTimedSerializer(app.secret_key, salt='edusurvey-account-import')

    @app.post('/api/admin/accounts/import-preview')
    @login_required(roles=['administrator'])
    def preview_import():
        data = request.get_json(silent=True)
        try:
            with get_db() as db:
                if not ready(db):
                    return fail('Account management requires the reviewed migration.', 503)
                rows = parse_import(db, data.get('csv') if isinstance(data, dict) else None)
            valid = not any(row['error'] for row in rows)
            ticket = serializer().dumps({'actor': session['user_id'], 'digest': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(), 'nonce': secrets.token_urlsafe(24)}) if valid else None
            return jsonify(rows=rows, valid=valid, confirmation=ticket)
        except (ValueError, csv.Error) as error:
            return fail(str(error))

    @app.post('/api/admin/accounts/import-confirm')
    @login_required(roles=['administrator'])
    def confirm_import():
        data = request.get_json(silent=True)
        try:
            if not isinstance(data, dict) or not isinstance(data.get('confirmation'), str):
                return fail('Preview this CSV before confirming.')
            ticket = serializer().loads(data['confirmation'], max_age=900)
            if ticket['actor'] != session['user_id']:
                return fail('This preview belongs to another administrator.', 403)
            with get_db() as db:
                if error := authorize(db):
                    return error
                rows = parse_import(db, data.get('csv'))
                if any(row['error'] for row in rows):
                    return fail('CSV has changed or an account now exists. Preview again.', 409)
                if hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest() != ticket['digest']:
                    return fail('CSV changed after preview. Preview again.', 409)
                if db.execute('SELECT 1 FROM account_imports WHERE nonce=?', (ticket['nonce'],)).fetchone():
                    return fail('This import was already confirmed.', 409)
                db.execute('INSERT INTO account_imports(nonce,actor_id,confirmed_at) VALUES (?,?,?)', (ticket['nonce'], session['user_id'], now_text()))
                accounts = [create_account(db, row) for row in rows]
            return jsonify(accounts=accounts, message='Accounts created. Deliver each setup link privately.'), 201
        except (BadSignature, KeyError, TypeError):
            return fail('Preview expired or invalid. Preview again.')
        except (ValueError, csv.Error) as error:
            return fail(str(error))

    @app.post('/api/admin/memberships')
    @login_required(roles=['administrator'])
    def change_membership():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or data.get('action') not in ('remove', 'transfer') or any(type(data.get(key)) is not int or data[key] < 1 for key in ('user_id', 'course_id')):
            return fail('Select a membership and remove or transfer.')
        with get_db() as db:
            if error := authorize(db):
                return error
            source = db.execute('SELECT role FROM users WHERE id=?', (data['user_id'],)).fetchone()
            if source is None or source['role'] not in {'student', 'lecturer'}:
                return fail('Membership not found.', 404)
            table, column = ('course_enrollments', 'student_id') if source['role'] == 'student' else ('course_lecturers', 'lecturer_id')
            values = (data['user_id'], data['course_id'])
            if not db.execute(f'SELECT 1 FROM {table} WHERE {column}=? AND course_id=?', values).fetchone():
                return fail('Membership not found.', 404)
            if data['action'] == 'transfer':
                target_id = data.get('target_id')
                if type(target_id) is not int or target_id == data['user_id']:
                    return fail('Select a different target account.')
                target = db.execute('SELECT role FROM users WHERE id=?', (target_id,)).fetchone()
                if target is None or target['role'] != source['role'] or access(db, target_id)['state'] == 'disabled':
                    return fail('Target must be an enabled account with the same role.')
                db.execute(f'INSERT INTO {table}({column},course_id) VALUES (?,?) ON CONFLICT({column},course_id) DO NOTHING', (target_id, data['course_id']))
            elif source['role'] == 'lecturer' and db.execute('SELECT COUNT(*) AS n FROM course_lecturers WHERE course_id=?', (data['course_id'],)).fetchone()['n'] <= 1 and db.execute("SELECT 1 FROM evaluations WHERE course_id=? AND status IN ('open','draft')", (data['course_id'],)).fetchone():
                return fail('Transfer the last lecturer while evaluations are open or draft.', 409)
            # Feedback remains attached to its original student and evaluation.
            db.execute(f'DELETE FROM {table} WHERE {column}=? AND course_id=?', values)
        return jsonify(message='Membership updated. Existing feedback was preserved.')
