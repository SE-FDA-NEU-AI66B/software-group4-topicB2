"""#205: persistent bootstrap and fail-closed release orchestration."""

import json
import sqlite3
from contextlib import closing
from io import BytesIO

import pytest

from tools import deploy_render, prepare_production


@pytest.fixture
def production_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUSURVEY_ENV", "production")
    monkeypatch.setenv("EDUSURVEY_SECRET_KEY", "synthetic-test-secret-" * 3)
    monkeypatch.setenv("EDUSURVEY_DATABASE", str(tmp_path / "demo.db"))
    monkeypatch.setenv("EDUSURVEY_DATA_MOUNT", str(tmp_path))
    monkeypatch.setenv("EDUSURVEY_BOOTSTRAP_DEMO", "1")
    monkeypatch.setattr(prepare_production.os.path, "ismount", lambda path: path == tmp_path)
    return tmp_path / "demo.db"


def test_production_restart_preserves_data(production_storage):
    prepare_production.prepare_database()
    with closing(sqlite3.connect(production_storage)) as db, db:
        db.execute("UPDATE courses SET course_name='Persistent marker' WHERE id=1")
    before = production_storage.read_bytes()
    prepare_production.prepare_database()
    assert production_storage.read_bytes() == before
    # Missing data after initial provision is a recovery event, never auto-reseed.
    production_storage.unlink()
    with pytest.raises(RuntimeError, match="restore backup"):
        prepare_production.prepare_database()
    assert not production_storage.exists()


@pytest.mark.parametrize("state", ["no-opt-in", "no-mount", "corrupt"])
def test_bootstrap_fails_closed(production_storage, monkeypatch, state):
    if state == "no-opt-in":
        monkeypatch.delenv("EDUSURVEY_BOOTSTRAP_DEMO")
    elif state == "no-mount":
        monkeypatch.setattr(prepare_production.os.path, "ismount", lambda path: False)
    else:
        production_storage.write_bytes(b"not a database")
    before = production_storage.read_bytes() if production_storage.exists() else None
    with pytest.raises((RuntimeError, sqlite3.DatabaseError)):
        prepare_production.prepare_database()
    assert (production_storage.read_bytes() if production_storage.exists() else None) == before


@pytest.fixture
def render_environment(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-synthetic")
    return monkeypatch


def test_deploy_rejects_pr_before_provider_call(render_environment):
    render_environment.setenv("GITHUB_EVENT_NAME", "pull_request")
    render_environment.setattr(deploy_render, "api", lambda *args: pytest.fail("Provider must not be called"))
    with pytest.raises(RuntimeError, match="main push"):
        deploy_render.deploy()


@pytest.mark.parametrize("state", ["auto-deploy", "wrong-repo", "wrong-sha", "failed-build", "ready"])
def test_deploy_exact_sha_and_readiness(render_environment, state):
    calls = []

    def fake_api(path, payload=None):
        calls.append((path, payload))
        if path == "services/srv-synthetic":
            return {"autoDeployTrigger": "commit" if state == "auto-deploy" else "off",
                    "branch": "main", "repo": "wrong" if state == "wrong-repo" else
                    "https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2",
                    "serviceDetails": {"url": "https://synthetic.onrender.com"}}
        if payload is not None:
            assert payload == {"commitId": "a" * 40}
            return {"id": "dep-synthetic"}
        return {"status": "build_failed" if state == "failed-build" else "live",
                "commit": {"id": "b" * 40 if state == "wrong-sha" else "a" * 40}}

    class HealthResponse(BytesIO):
        status = 200

    render_environment.setattr(deploy_render, "api", fake_api)
    render_environment.setattr(deploy_render.urllib.request, "urlopen", lambda *args, **kwargs: HealthResponse(
        json.dumps({"status": "ok", "database": "ok"}).encode()))
    if state == "ready":
        deploy_render.deploy()
    else:
        with pytest.raises(RuntimeError):
            deploy_render.deploy()
    if state in {"auto-deploy", "wrong-repo"}:
        assert len(calls) == 1  # Reject configuration before triggering a deployment.
