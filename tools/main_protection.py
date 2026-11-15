"""Read active main rules; an administrator may explicitly apply the reviewed ruleset."""

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

REPOSITORY = "SE-FDA-NEU-AI66B/software-group4-topicB2"
PAYLOAD = Path(__file__).resolve().parents[1] / ".github/main-protection.json"
REQUIRED_CHECKS = {"CI gate", "Python tests", "No secrets committed"}


def api(path, method="GET", payload=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "EduSurvey-main-protection"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        "https://api.github.com/" + path, headers=headers, method=method,
        data=None if payload is None else json.dumps(payload).encode(),
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub returned HTTP {error.code}; no protection change is certified.") from None


def protection_summary(rules):
    approvals = max((r.get("parameters", {}).get("required_approving_review_count", 0)
                     for r in rules if r["type"] == "pull_request"), default=0)
    required = {check["context"] for rule in rules if rule["type"] == "required_status_checks"
                and rule.get("parameters", {}).get("strict_required_status_checks_policy")
                for check in rule["parameters"].get("required_status_checks", [])
                if check.get("integration_id") == 15368}
    missing = sorted(REQUIRED_CHECKS - required)
    return {"approval_count": approvals, "required_checks": sorted(required),
            "missing_checks": missing, "verified": approvals >= 1 and not missing}


def apply_ruleset():
    # Credentials are read from the administrator's secret environment, never arguments/logs.
    if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        raise RuntimeError("Administrator token required in GH_TOKEN or GITHUB_TOKEN; do not paste it into logs.")
    if not api(f"repos/{REPOSITORY}").get("permissions", {}).get("admin"):
        raise RuntimeError("Repository admin access is required; no ruleset was changed.")
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    existing = [r for r in api(f"repos/{REPOSITORY}/rulesets")
                if r["name"] == payload["name"] and r["source_type"] == "Repository"]
    if len(existing) > 1:
        raise RuntimeError("Duplicate rulesets require administrator inspection before changing protection.")
    if existing:
        return api(f"repos/{REPOSITORY}/rulesets/{existing[0]['id']}", "PUT", payload)
    return api(f"repos/{REPOSITORY}/rulesets", "POST", payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Administrator only: apply the reviewed supplemental repository ruleset.")
    args = parser.parse_args()
    if args.apply:
        apply_ruleset()
    summary = protection_summary(api(f"repos/{REPOSITORY}/rules/branches/main"))
    print(json.dumps(summary, sort_keys=True))
    if not summary["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
