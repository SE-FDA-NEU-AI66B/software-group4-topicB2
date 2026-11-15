"""M5-DOC01/02: incomplete or inconsistent release data cannot become a final PDF."""

import json
from pathlib import Path

import pytest

from tools.build_m5_submission import REQUIRED_CONFIRMATIONS, final_errors, render_html


def complete_example():
    """Synthetic formatting fixture only; not evidence of a real release/team."""
    repo = "https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2"
    return {
        "team_number": 99, "product": "Synthetic fixture",
        "members": [{"name": f"Fixture {i}", "student_id": f"FIXTURE-{i}"} for i in range(3)],
        "scrum_master": "khuatnhatminhcfpro-cmyk", "repository": repo,
        "public_url": "https://fixture-edusurvey.onrender.com", "release_url": repo + "/releases/tag/v1.0",
        "release_sha": "a" * 40, "deployed_sha": "a" * 40,
        "main_ci_url": repo + "/actions/runs/123", "test_accounts_url": repo + "/blob/main/README.md",
        "late_submission_agreement": "Synthetic acknowledgement; not a real instructor agreement.",
        "confirmations": dict.fromkeys(REQUIRED_CONFIRMATIONS, True),
    }


def test_committed_pending_data_refuses_final():
    """M5-DOC01: real pending metadata renders only a clearly labelled draft."""
    data = json.loads(Path("docs/m5/submission.json").read_text())
    assert final_errors(data)
    with pytest.raises(ValueError):
        render_html(data, final=True)
    content = render_html(data)
    assert "DRAFT — NOT READY FOR SUBMISSION" in content
    assert "Running app:" in content and "student ID pending" in content


@pytest.mark.parametrize("change", [
    {"team_number": None}, {"deployed_sha": "b" * 40},
    {"public_url": "http://localhost:5000"}, {"public_url": "https://127.0.0.1"},
    {"public_url": "https://10.0.0.1"}, {"public_url": "https://demo.invalid"}, {"release_url": None},
    {"late_submission_agreement": None}, {"confirmations": {}},
])
def test_incomplete_final_is_rejected(change):
    """M5-DOC02: missing confirmation, identity or source alignment blocks final mode."""
    data = complete_example()
    data.update(change)
    with pytest.raises(ValueError):
        render_html(data, final=True)


def test_formatter_escapes_text_and_uses_supplied_metadata():
    """M5-DOC03: validated fixture renders literal text, not injected HTML."""
    data = complete_example()
    data["members"][0]["name"] = '<script>alert("x")</script>'
    content = render_html(data, final=True)
    assert "<script>" not in content
    assert "&lt;script&gt;" in content
    assert "DRAFT —" not in content


@pytest.mark.parametrize("identifier", ["PENDING", "FIXTURE-1"])
def test_placeholder_or_duplicate_student_ids_are_rejected(identifier):
    """M5-DOC04: placeholders/duplicates cannot hide behind checked confirmations."""
    data = complete_example()
    data["members"][0]["student_id"] = identifier
    with pytest.raises(ValueError):
        render_html(data, final=True)
