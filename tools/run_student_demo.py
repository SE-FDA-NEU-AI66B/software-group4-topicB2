"""Run a disposable local P0 demo without touching data/edusurvey.db."""

import argparse
import secrets
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import app as app_module
from src import init_db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="edusurvey-demo-") as directory:
        init_db.DB_DIR = Path(directory)
        init_db.DB_PATH = init_db.DB_DIR / "demo.db"
        init_db.initialize_database()
        with closing(sqlite3.connect(init_db.DB_PATH)) as db, db:
            # The original course examples have fixed, historical deadlines.
            # Make exactly one sample available for a fresh student's walkthrough.
            db.execute("DELETE FROM response_answers WHERE response_id IN (SELECT id FROM responses WHERE student_id = 1 AND evaluation_id = 1)")
            db.execute("DELETE FROM responses WHERE student_id = 1 AND evaluation_id = 1")
            db.execute("UPDATE evaluations SET status = 'open', deadline = ? WHERE id = 1", ((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),))
        app_module.DATABASE = init_db.DB_PATH
        app_module.app.config["SECRET_KEY"] = secrets.token_hex(32)
        print(f"Disposable demo: http://127.0.0.1:{args.port}/ (data removed on exit)", flush=True)
        app_module.app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
