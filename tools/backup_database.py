"""Create an SQLite online backup without overwriting a destination."""

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path


def backup_database(source, destination):
    source, destination = Path(source), Path(destination)
    # Fail before creating any output if the source is missing or invalid.
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as original:
        if original.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("Source integrity check failed")
        if original.execute("PRAGMA foreign_key_check").fetchall():
            raise sqlite3.IntegrityError("Source foreign-key check failed")
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        try:
            with closing(sqlite3.connect(destination)) as backup:
                original.backup(backup)
                if backup.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise sqlite3.DatabaseError("Backup integrity check failed")
                if backup.execute("PRAGMA foreign_key_check").fetchall():
                    raise sqlite3.IntegrityError("Backup foreign-key check failed")
        except Exception:
            destination.unlink(missing_ok=True)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    backup_database(args.source, args.destination)
    print("Backup created and integrity checked. Treat the backup as private data.")


if __name__ == "__main__":
    main()
