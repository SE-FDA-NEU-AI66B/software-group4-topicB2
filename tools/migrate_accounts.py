"""Apply the reviewed additive account schema explicitly; never runs at startup."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.account_store import migrate_accounts
from src.database import DATABASE_ERRORS

MIGRATION_ERRORS = (*DATABASE_ERRORS, RuntimeError, ValueError, OSError)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', help='Existing SQLite path; use EDUSURVEY_MIGRATION_DATABASE for PostgreSQL URLs.')
    parser.add_argument('--apply', action='store_true', required=True)
    args = parser.parse_args()
    database = args.database or os.environ.get('EDUSURVEY_MIGRATION_DATABASE')
    if not database:
        parser.error('Provide a reviewed migration database.')
    try:
        migrate_accounts(database)
    except MIGRATION_ERRORS:
        raise SystemExit('Account migration failed; no credentials or database details are logged.') from None
    print('Additive account schema verified. Existing users and feedback preserved.')
