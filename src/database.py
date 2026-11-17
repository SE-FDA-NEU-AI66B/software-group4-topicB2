"""Small DB-API boundary: SQLite locally, PostgreSQL for external storage.

Only parameter tokens are translated. Dialect-dependent SQL lives in explicit
helpers, never in global SQL text replacements. Values remain bound parameters.
"""
import re
import sqlite3
from decimal import Decimal
from pathlib import Path

if __package__:
    from .pg_driver import PostgresError, dict_row, psycopg
    from .runtime import TransactionConnection
else:
    from pg_driver import PostgresError, dict_row, psycopg
    from runtime import TransactionConnection


def api_row(cursor):
    make_row = dict_row(cursor)
    def build(values):
        return {key: float(value) if isinstance(value, Decimal) else value
                for key, value in make_row(values).items()}
    return build


DATABASE_ERRORS = (sqlite3.Error, PostgresError)
TABLES = ("users", "courses", "course_enrollments", "course_lecturers",
          "evaluations", "questions", "responses", "response_answers", "deadline_reminders")


def is_postgres(database):
    return isinstance(database, str) and database.startswith(("postgresql://", "postgres://"))


# Strings, quoted identifiers and comments must retain literal ? / : / % chars.
TOKENS = re.compile(r"('(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|--[^\n]*|/\*[\s\S]*?\*/|::|:[A-Za-z_]\w*|\?)")


def bind_sql(statement, parameters):
    parts = TOKENS.split(statement)
    for i, token in enumerate(parts):
        token = token.replace('%', '%%')
        if i % 2 and token == '?':
            token = '%s'
        elif i % 2 and token.startswith(':') and token != '::':
            token = '%(' + token[1:] + ')s'
        parts[i] = token
    return ''.join(parts)


class Cursor:
    def __init__(self, cursor, lastrowid=None):
        self.cursor = cursor
        self.lastrowid = lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()


class PostgresConnection:
    dialect = 'postgresql'

    def __init__(self, database):
        if psycopg is None:
            raise PostgresError('Install requirements-postgres.txt for PostgreSQL support.')
        self.raw = psycopg.connect(database, row_factory=api_row, connect_timeout=5,
                                   prepare_threshold=None)
        try:
            self.raw.execute("SET LOCAL TIME ZONE 'UTC'")
            self.raw.execute("SET LOCAL lock_timeout = '5s'")
            self.raw.execute("SET LOCAL statement_timeout = '15s'")
        except PostgresError:
            self.raw.close()
            raise

    def execute(self, statement, parameters=()):
        cursor = self.raw.execute(bind_sql(statement, parameters), parameters)
        return Cursor(cursor)

    def insert_id(self, statement, parameters):
        return self.execute(statement + ' RETURNING id', parameters).fetchone()['id']

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.raw.__exit__(*args)

    def close(self):
        self.raw.close()


def connect(database):
    if is_postgres(database):
        return PostgresConnection(database)
    connection = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=rw',
                                 uri=True, factory=TransactionConnection, timeout=5)
    connection.execute('PRAGMA foreign_keys = ON')
    connection.row_factory = sqlite3.Row
    return connection


def insert_id(connection, statement, parameters):
    if isinstance(connection, PostgresConnection):
        return connection.insert_id(statement, parameters)
    return connection.execute(statement, parameters).lastrowid


def reserve_submission(connection, evaluation_id, student_id):
    if isinstance(connection, PostgresConnection):
        # Transaction-scoped lock also covers the absent-response case. READ
        # COMMITTED sees the winning tab's commit after the lock is acquired.
        connection.execute('SELECT pg_advisory_xact_lock_shared(hashtextextended(?, 0))',
                           (f'edusurvey/evaluation/{evaluation_id}',))
        connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(?, 0))',
                           (f'edusurvey/submission/{evaluation_id}/{student_id}',))
    else:
        connection.execute('BEGIN IMMEDIATE')


def check_postgres(database):
    with connect(database) as connection:
        for table in TABLES:
            connection.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchone()
        version = connection.execute('SELECT version FROM edusurvey_migrations').fetchall()
        if version != [{'version': 1}]:
            raise PostgresError('Unsupported schema version')
