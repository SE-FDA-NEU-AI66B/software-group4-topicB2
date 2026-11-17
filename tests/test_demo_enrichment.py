"""Idempotent additive synthetic demo fixture."""
import sqlite3

from src import app as app_module
from tools.enrich_demo import enrich


def test_enrichment_idempotent_and_preserves_existing(api_client):
    with sqlite3.connect(app_module.DATABASE) as db:
        before = db.execute('SELECT * FROM evaluations WHERE id=1').fetchone()
    counts = enrich(app_module.DATABASE, 'Synthetic-test-credential')
    assert counts == {'users': 37, 'courses': 24, 'evaluations': 24, 'responses': 264}
    assert enrich(app_module.DATABASE, 'Another-test-credential') == dict.fromkeys(counts, 0)
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT * FROM evaluations WHERE id=1').fetchone() == before
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert db.execute("SELECT COUNT(*) FROM questions WHERE evaluation_id>1").fetchone()[0] == 120

