"""Production configuration, database readiness and sanitized request telemetry."""

import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from flask import g, jsonify, request
from werkzeug.exceptions import HTTPException

if __package__:
    from .pg_driver import PostgresError
else:
    from pg_driver import PostgresError


def log_runtime_error(app, event, error=None):
    """Correlate internal error categories without exception messages or user input."""
    record = {
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "request_id": g.request_id,
        "endpoint": request.endpoint or "unmatched",
    }
    if error is not None:
        record["error_type"] = type(error).__name__
    app.logger.error(json.dumps(record, sort_keys=True))


class TransactionConnection(sqlite3.Connection):
    """Commit/roll back a context-managed transaction and always close its handle."""

    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def configure_runtime(app, default_database):
    production = os.environ.get("EDUSURVEY_ENV") == "production"
    secret = os.environ.get("EDUSURVEY_SECRET_KEY", "dev-only-secret-change-before-deployment")
    database = os.environ.get("EDUSURVEY_DATABASE", str(default_database))
    url = os.environ.get("DATABASE_URL")
    postgres_required = os.environ.get("EDUSURVEY_DATABASE_BACKEND") == "postgresql" or os.environ.get("RENDER") == "true"
    if url:
        from urllib.parse import parse_qs, urlsplit
        try:
            parsed = urlsplit(url)
            valid = parsed.scheme in {"postgres", "postgresql"} and parsed.hostname and parsed.path.strip("/")
            if production:
                valid = valid and parse_qs(parsed.query).get("sslmode", [None])[0] in {"require", "verify-ca", "verify-full"}
        except ValueError:
            valid = False
        if not valid:
            raise RuntimeError("Invalid PostgreSQL configuration; production requires SSL.")
    if production and postgres_required and not url:
        raise RuntimeError("Production PostgreSQL requires DATABASE_URL; SQLite fallback is disabled.")
    if production:
        if len(secret) < 32 or secret == "dev-only-secret-change-before-deployment":
            raise RuntimeError("Production requires EDUSURVEY_SECRET_KEY with at least 32 characters.")
        if not url and (not os.environ.get("EDUSURVEY_DATABASE") or not Path(database).is_absolute()):
            raise RuntimeError("Production requires an absolute EDUSURVEY_DATABASE path on persistent storage.")
    app.config.update(
        SECRET_KEY=secret,
        DATABASE=url or database,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
    )
    # Werkzeug access logs include raw URLs/query strings; use our safe telemetry.
    if production:
        import logging
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        app.logger.setLevel(logging.INFO)
    return url or Path(database)


def register_runtime(app, database_path):
    @app.before_request
    def start_request_timer():
        g.request_started = perf_counter()
        # Never trust/reflect client-supplied correlation IDs (may contain private input).
        g.request_id = uuid4().hex

    @app.after_request
    def record_request(response):
        duration = max(0.0, (perf_counter() - g.request_started) * 1000)
        app.logger.info(json.dumps({
            "event": "request_completed",
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "request_id": g.request_id,
            "endpoint": request.endpoint or "unmatched",
            "method": request.method if request.method in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"} else "OTHER",
            "status": response.status_code,
            "duration_ms": round(duration, 3),
        }, sort_keys=True))
        response.headers["X-Request-ID"] = g.request_id
        return response

    @app.errorhandler(Exception)
    def unexpected_failure(error):
        if isinstance(error, HTTPException):
            return error
        log_runtime_error(app, "request_failed", error)
        return jsonify({"error": {
            "code": "INTERNAL_ERROR",
            "message": "The service could not complete this request.",
            "action": "Try again; contact the administrator if the problem continues.",
        }}), 500

    @app.get("/health")
    def health():
        try:
            if __package__:
                from .database import check_postgres, is_postgres
            else:
                from database import check_postgres, is_postgres
            if is_postgres(database_path()):
                check_postgres(database_path())
                response = jsonify({"status": "ok", "database": "ok"})
                response.headers["Cache-Control"] = "no-store"
                return response, 200
            # Read-only mode never creates an empty replacement DB when a mount is missing.
            uri = Path(database_path()).resolve().as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True, timeout=2)) as connection:
                for table in ("users", "courses", "course_enrollments", "course_lecturers",
                              "evaluations", "questions", "responses", "response_answers"):
                    connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
                if connection.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok":
                    raise sqlite3.DatabaseError("Database integrity check failed")
                if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise sqlite3.DatabaseError("Database relationship check failed")
            response = jsonify({"status": "ok", "database": "ok"})
            status = 200
        except (sqlite3.Error, OSError, ValueError, PostgresError):
            log_runtime_error(app, "database_unavailable")
            response = jsonify({"status": "unavailable", "database": "unavailable"})
            status = 503
        response.headers["Cache-Control"] = "no-store"
        return response, status
