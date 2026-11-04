"""Shared pytest fixtures for isolated application tests."""

import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import app as app_module  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a Flask test client backed by a temporary SQLite database."""
    database = tmp_path / "test_edusurvey.db"
    monkeypatch.setattr(app_module, "DATABASE", database)

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "student1@edusurvey.edu",
                generate_password_hash("Password123!"),
                "Minh Nguyen",
                "student",
            ),
        )

    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    with app_module.app.test_client() as test_client:
        yield test_client
