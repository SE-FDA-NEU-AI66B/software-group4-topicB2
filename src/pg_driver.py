"""Optional driver: the original SQLite-only installation remains supported."""
try:
    import psycopg
    from psycopg.rows import dict_row
    PostgresError = psycopg.Error
except ImportError:
    psycopg = None
    dict_row = None

    class PostgresError(Exception):
        """Driver unavailable; SQLite code never raises this exception."""
