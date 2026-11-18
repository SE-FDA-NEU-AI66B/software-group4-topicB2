"""Optional additive lifecycle schema and shared authorization state.

Legacy accounts remain active when no lifecycle row/schema exists. No runtime DDL.
"""
from datetime import UTC, datetime

TABLE_NAMES = {'account_access', 'account_tokens', 'account_imports', 'account_schema'}


def ready(db):
    if getattr(db, 'dialect', '') == 'postgresql':
        return db.execute("SELECT to_regclass('account_access') AS name").fetchone()['name'] is not None
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_access'").fetchone() is not None


def access(db, user_id):
    if not ready(db):
        return {'state': 'active', 'version': 0}
    row = db.execute('SELECT state,version FROM account_access WHERE user_id=?', (user_id,)).fetchone()
    return dict(row) if row else {'state': 'active', 'version': 0}


def lock_admin(db):
    if getattr(db, 'dialect', '') == 'postgresql':
        db.execute("SELECT pg_advisory_xact_lock(hashtextextended('edusurvey/admin-roles', 0))")
    else:
        db.execute('BEGIN IMMEDIATE')


def active_admins(db):
    if not ready(db):
        return db.execute("SELECT COUNT(*) AS n FROM users WHERE role='administrator'").fetchone()['n']
    return db.execute("SELECT COUNT(*) AS n FROM users u LEFT JOIN account_access a ON a.user_id=u.id WHERE u.role='administrator' AND (a.state IS NULL OR a.state='active')").fetchone()['n']


def now_text():
    return datetime.now(UTC).isoformat()


def migrate_accounts(database):
    """Explicit transaction, idempotent verification; existing users are not updated."""
    if __package__:
        from .database import connect
    else:
        from database import connect
    with connect(database) as db:
        lock_admin(db)
        integer = 'BIGINT' if getattr(db, 'dialect', '') == 'postgresql' else 'INTEGER'
        statements = [
            f'''CREATE TABLE IF NOT EXISTS account_access (
                user_id {integer} PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                state TEXT NOT NULL CHECK(state IN ('active','invited','disabled')),
                version {integer} NOT NULL DEFAULT 0 CHECK(version >= 0),
                resume_state TEXT NOT NULL DEFAULT 'active' CHECK(resume_state IN ('active','invited')),
                updated_at TEXT NOT NULL)''',
            f'''CREATE TABLE IF NOT EXISTS account_tokens (
                digest TEXT PRIMARY KEY,
                user_id {integer} NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                purpose TEXT NOT NULL CHECK(purpose IN ('invite','reset')),
                expires_at TEXT NOT NULL,
                consumed_at TEXT)''',
            f'''CREATE TABLE IF NOT EXISTS account_imports (
                nonce TEXT PRIMARY KEY, actor_id {integer} NOT NULL REFERENCES users(id),
                confirmed_at TEXT NOT NULL)''',
            '''CREATE TABLE IF NOT EXISTS account_schema (version INTEGER PRIMARY KEY CHECK(version=1))''',
        ]
        for statement in statements:
            db.execute(statement)
        db.execute('INSERT INTO account_schema(version) VALUES (1) ON CONFLICT(version) DO NOTHING')
        # Verify expected fields, including on repeat application; no destructive repair.
        db.execute('SELECT user_id,state,version,resume_state,updated_at FROM account_access LIMIT 0')
        db.execute('SELECT digest,user_id,purpose,expires_at,consumed_at FROM account_tokens LIMIT 0')
        db.execute('SELECT nonce,actor_id,confirmed_at FROM account_imports LIMIT 0')
