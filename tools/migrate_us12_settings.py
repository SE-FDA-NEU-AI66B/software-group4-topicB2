"""Add only the US12 settings table to an existing DB; never reset or seed it."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from src.admin import SETTINGS_TABLE


def migrate(database):
    uri = Path(database).resolve().as_uri() + "?mode=rw"
    with closing(sqlite3.connect(uri, uri=True)) as connection, connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("SELECT id, role FROM users LIMIT 1")
        connection.execute(SETTINGS_TABLE)
        connection.execute("SELECT key,value,updated_by,updated_at FROM system_settings LIMIT 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    migrate(parser.parse_args().database)
    print("US12 settings migration complete; existing records preserved.")
