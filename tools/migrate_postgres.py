"""Explicit, atomic, versioned initialization of a NEW PostgreSQL database.

No implicit startup migration. Uses DIRECT_URL; never prints a connection URL.
A nonempty or unknown schema is refused. Reapplication verifies the checksum.
"""
import argparse
import hashlib
import os
from pathlib import Path

from src.database import TABLES
from src.pg_driver import PostgresError, psycopg

MIGRATION = Path(__file__).resolve().parents[1] / 'src/postgresql/001_initial.sql'


def migrate(url):
    script = MIGRATION.read_text()
    checksum = hashlib.sha256(script.encode()).hexdigest()
    if psycopg is None:
        raise RuntimeError('Install requirements-postgres.txt.')
    with psycopg.connect(url, connect_timeout=5) as db:
        db.execute('SELECT pg_advisory_xact_lock(19780423)')
        tables = {r[0] for r in db.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
        )}
        if tables:
            if tables != set(TABLES) | {'edusurvey_migrations'}:
                raise RuntimeError('Refusing migration of a nonempty or unknown schema.')
            if db.execute('SELECT version, checksum FROM edusurvey_migrations').fetchall() != [(1, checksum)]:
                raise RuntimeError('Schema version/checksum mismatch; manual review required.')
            return
        db.execute(script, prepare=False)
        db.execute('INSERT INTO edusurvey_migrations VALUES (1, %s)', (checksum,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new-database', action='store_true', required=True)
    parser.parse_args()
    try:
        url = os.environ.get('DIRECT_URL')
        if not url:
            raise RuntimeError('DIRECT_URL must be configured securely.')
        migrate(url)
    except (PostgresError, RuntimeError, ValueError):
        raise SystemExit('Migration refused or unavailable; inspect configuration without logging secrets.') from None
    print('Schema version 1 verified; existing data preserved.')


if __name__ == '__main__':
    main()
