"""Seed only freshly generated synthetic data into an empty migrated database.

Never reads data/edusurvey.db. No reseeding on deployment or existing rows.
"""
import argparse
import os
import sqlite3
import tempfile
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path

from src.database import TABLES
from src.pg_driver import PostgresError, psycopg
from tools.migrate_postgres import migrate

sql = psycopg.sql if psycopg else None


def copy_snapshot(source, url):
    """Copy a caller-owned isolated snapshot atomically, preserving IDs/FKs.

    Low-level helper; no CLI for arbitrary/private SQLite sources is exposed.
    Caller must classify/backup/authorize any future real-data transfer first.
    """
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as old:
        if old.execute('PRAGMA integrity_check').fetchall() != [('ok',)] or old.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Invalid source snapshot.')
        manifest = {t: old.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in TABLES}
        with psycopg.connect(url, connect_timeout=5) as db:
            db.execute('SELECT pg_advisory_xact_lock(19780423)')
            db.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE').format(
                sql.SQL(', ').join(map(sql.Identifier, TABLES))))
            if any(db.execute(sql.SQL('SELECT 1 FROM {} LIMIT 1').format(sql.Identifier(t))).fetchone() for t in TABLES):
                raise RuntimeError('Refusing to seed a nonempty database.')
            for table in TABLES:
                cursor = old.execute(f'SELECT * FROM {table} ORDER BY id')
                columns = [c[0] for c in cursor.description]
                statement = sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
                    sql.Identifier(table), sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(sql.Placeholder() for _ in columns))
                for row in cursor:
                    db.execute(statement, row)
                count = db.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
                if count != manifest[table]:
                    raise RuntimeError('Migration count mismatch; transaction rolled back.')
            # Restart identities transactionally; setval() itself is not rollback-safe.
            for table in TABLES:
                maximum = db.execute(sql.SQL('SELECT COALESCE(MAX(id), 0) FROM {}').format(sql.Identifier(table))).fetchone()[0]
                sequence = old.execute('SELECT seq FROM sqlite_sequence WHERE name=?', (table,)).fetchone()
                # AUTOINCREMENT never reuses deleted IDs. MAX(id) alone loses
                # SQLite's historical high watermark after deletions.
                next_id = max(maximum, sequence[0] if sequence else 0) + 1
                db.execute(sql.SQL('ALTER TABLE {} ALTER COLUMN id RESTART WITH {}').format(
                    sql.Identifier(table), sql.Literal(next_id)))
        return manifest


def seed_demo(url):
    from src import init_db
    migrate(url)
    with tempfile.TemporaryDirectory(prefix='edusurvey-synthetic-') as directory:
        original = init_db.DB_PATH, init_db.DB_DIR
        source = Path(directory) / 'synthetic.db'
        try:
            init_db.DB_PATH, init_db.DB_DIR = source, source.parent
            with redirect_stdout(StringIO()):
                init_db.initialize_database(m5_demo=True)
        finally:
            init_db.DB_PATH, init_db.DB_DIR = original
        return copy_snapshot(source, url)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new-synthetic-demo', action='store_true', required=True)
    parser.parse_args()
    try:
        url = os.environ.get('DIRECT_URL')
        if not url:
            raise RuntimeError('DIRECT_URL required.')
        counts = seed_demo(url)
    except (PostgresError, sqlite3.Error, RuntimeError, ValueError):
        raise SystemExit('Demo initialization refused or unavailable; no credentials logged.') from None
    print('New synthetic demo ready. Row counts:', counts)


if __name__ == '__main__':
    main()
