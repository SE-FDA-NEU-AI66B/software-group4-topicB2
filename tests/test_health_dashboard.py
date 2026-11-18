"""The presentation shell never replaces readiness JSON/status or needs a DB."""
from src import app as app_module


def test_dashboard_preserves_readiness_contract(api_client):
    page = api_client.get('/health/dashboard')
    assert page.status_code == 200 and page.mimetype == 'text/html'
    assert page.headers['Cache-Control'] == 'no-store'
    assert 'Application Status' in page.text and 'Database Status' in page.text
    health = api_client.get('/health', headers={'Accept': 'text/html'})
    assert health.status_code == 200 and health.mimetype == 'application/json'
    assert health.json == {'status': 'ok', 'database': 'ok'}


def test_dashboard_survives_database_outage_with_signed_session(api_client, monkeypatch, tmp_path):
    missing = tmp_path / 'never-created.db'
    with api_client.session_transaction() as session:
        session['user_id'], session['role'] = 1, 'student'
    monkeypatch.setattr(app_module, 'DATABASE', missing)
    page = api_client.get('/health/dashboard')
    assert page.status_code == 200 and page.mimetype == 'text/html'
    health = api_client.get('/health')
    assert health.status_code == 503 and health.mimetype == 'application/json'
    assert health.json == {'status': 'unavailable', 'database': 'unavailable'}
    assert not missing.exists()
