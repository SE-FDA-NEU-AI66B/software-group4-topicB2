"""#207 / #200: failures, skipped required jobs and non-main events cannot release."""

from pathlib import Path

import pytest
import yaml

from tools import ci_gate, deploy_render, main_protection

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def green_results():
    return {"DETECT_RESULT": "success", "PYTHON_RESULT": "success",
            "SECURITY_RESULT": "success", "NODE_DETECTED": "false", "NODE_RESULT": "skipped"}


@pytest.mark.parametrize("job", ["DETECT_RESULT", "PYTHON_RESULT", "SECURITY_RESULT"])
@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", ""])
def test_required_ci_job_cannot_be_bypassed(green_results, job, result):
    green_results[job] = result
    with pytest.raises(RuntimeError, match="Required CI job"):
        ci_gate.require_successful_checks(green_results)


@pytest.mark.parametrize("detected,result,valid", [
    ("false", "skipped", True), ("true", "success", True),
    ("true", "failure", False), ("true", "skipped", False),
    ("false", "failure", False), ("", "skipped", False),
])
def test_optional_stack_does_not_hide_failure(green_results, detected, result, valid):
    green_results.update(NODE_DETECTED=detected, NODE_RESULT=result)
    if valid:
        ci_gate.require_successful_checks(green_results)
    else:
        with pytest.raises(RuntimeError):
            ci_gate.require_successful_checks(green_results)


@pytest.mark.parametrize("gate_result", [None, "failure", "cancelled", "skipped"])
def test_deploy_rejects_non_green_gate_before_provider_call(monkeypatch, gate_result):
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-synthetic")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    if gate_result is None:
        monkeypatch.delenv("CI_GATE_RESULT", raising=False)
    else:
        monkeypatch.setenv("CI_GATE_RESULT", gate_result)
    monkeypatch.setattr(deploy_render, "api", lambda *args: pytest.fail("Provider must not be contacted"))
    with pytest.raises(RuntimeError, match="CI gate must succeed"):
        deploy_render.deploy()


def test_production_workflow_retains_full_suite_and_security_gate():
    # BaseLoader preserves GitHub's `on` key rather than treating it as YAML 1.1 True.
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    jobs = workflow["jobs"]
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["on"]) == {"push", "pull_request"}
    assert jobs["gate"]["if"] == "always()"
    assert set(jobs["gate"]["needs"]) == {"detect", "python", "node", "secrets"}
    assert jobs["deploy"]["needs"] == ["gate"]
    assert jobs["deploy"]["environment"] == "production"
    condition = jobs["deploy"]["if"]
    assert "github.event_name == 'push'" in condition
    assert "github.ref == 'refs/heads/main'" in condition
    assert "vars.RENDER_DEPLOY_ENABLED == 'true'" in condition
    test_step = next(s for s in jobs["python"]["steps"] if s.get("name") == "Test")
    assert test_step["run"] == "python -m pytest -v --cov --cov-report=term-missing --junitxml=junit.xml"
    assert "continue-on-error" not in test_step
    lint = next(s for s in jobs["python"]["steps"] if s.get("name") == "Lint")
    assert "continue-on-error" not in lint
    assert len(jobs["secrets"]["steps"]) == 3
    deploy = next(s for s in jobs["deploy"]["steps"] if s.get("name") == "Deploy exact tested SHA and verify readiness")
    assert deploy["env"]["CI_GATE_RESULT"] == "${{ needs.gate.result }}"
    for job_id, job in jobs.items():
        if job_id != "deploy":
            assert "secrets.RENDER_API_KEY" not in str(job)


def test_current_approval_only_rules_are_not_reported_as_ci_protection():
    summary = main_protection.protection_summary([
        {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
    ])
    assert summary["verified"] is False
    assert summary["missing_checks"] == sorted(main_protection.REQUIRED_CHECKS)


@pytest.mark.parametrize("strict,app_id,valid", [(True, 15368, True), (False, 15368, False), (True, 42, False)])
def test_required_checks_must_be_strict_and_from_actions(strict, app_id, valid):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
             {"type": "required_status_checks", "parameters": {
                 "strict_required_status_checks_policy": strict,
                 "required_status_checks": [{"context": name, "integration_id": app_id}
                                            for name in main_protection.REQUIRED_CHECKS],
             }}]
    assert main_protection.protection_summary(rules)["verified"] is valid


def test_non_admin_cannot_apply_ruleset(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "synthetic-test-value-not-a-real-token")
    calls = []

    def fake_api(path, method="GET", payload=None):
        calls.append((path, method))
        return {"permissions": {"admin": False}}

    monkeypatch.setattr(main_protection, "api", fake_api)
    with pytest.raises(RuntimeError, match="admin access"):
        main_protection.apply_ruleset()
    assert calls == [(f"repos/{main_protection.REPOSITORY}", "GET")]


@pytest.mark.parametrize("filename,allowed", [
    (".env", False), (".env.production", False), ("nested/.env.local", False),
    ("data/demo.db", False), ("data/demo.sqlite3", False), ("backup.dump", False),
    ("service.pem", False), ("service.key", False),
    (".env.example", True), ("src/schema.sql", True),
    ("src/feedback_queries.sql", True), ("README.md", True),
])
def test_ci_rejects_sensitive_tracked_files(tmp_path, filename, allowed):
    """M5-OPS01: even force-added env/DB/key files cannot bypass the CI guard."""
    import subprocess

    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    step = next(s for s in workflow["jobs"]["secrets"]["steps"] if s.get("name") == "No .env or database dumps")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic fixture only\n")
    subprocess.run(["git", "add", "--", filename], cwd=tmp_path, check=True)
    result = subprocess.run(["bash", "-eo", "pipefail", "-c", step["run"]], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert (result.returncode == 0) is allowed, result.stdout + result.stderr
