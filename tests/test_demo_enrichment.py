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



def test_rich_pack_is_additive_configurable_and_idempotent(api_client):
    from tools.enrich_demo import RICH_QUESTIONS
    with sqlite3.connect(app_module.DATABASE) as db:
        before = db.execute('SELECT * FROM response_answers ORDER BY id').fetchall()
    counts = enrich(app_module.DATABASE, 'Synthetic-rich-credential', rich=True)
    assert counts == {'users': 37, 'courses': 6, 'evaluations': 6, 'responses': 66}
    assert enrich(app_module.DATABASE, 'Synthetic-rich-credential', rich=True) == dict.fromkeys(counts, 0)
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT * FROM response_answers WHERE response_id=1 ORDER BY id').fetchall() == before
        assert db.execute('SELECT COUNT(*) FROM questions WHERE evaluation_id>1').fetchone()[0] == 6 * len(RICH_QUESTIONS)
        assert db.execute('SELECT COUNT(*) FROM questions WHERE evaluation_id>1 AND is_required=0').fetchone()[0] == 12
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_rich_pack_custom_question_count(api_client):
    questions = [{'question_text': f'Custom question {i}', 'question_type': 'rating'} for i in range(12)]
    enrich(app_module.DATABASE, 'Synthetic-rich-credential', rich=True, questions=questions)
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM questions WHERE evaluation_id>1').fetchone()[0] == 72
