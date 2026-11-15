"""Render an explicitly marked draft; final mode rejects incomplete release metadata.

This formats supplied evidence, not an independent deployment/rehearsal attestation.
It never tags, publishes a release, uploads a PDF, or changes an application database.
"""

import argparse
import html
import ipaddress
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

REPO = "https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2"
REQUIRED_CONFIRMATIONS = (
    "team_details_confirmed", "independent_review_and_merge", "green_main_ci",
    "provider_sha_and_public_p0_verified", "links_and_live_availability_verified",
    "twelve_minute_team_rehearsal_completed", "late_submission_arrangement_confirmed",
)


def public_https(value):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    if parsed.hostname:
        try:
            if not ipaddress.ip_address(parsed.hostname).is_global:
                return False
        except ValueError:
            if "." not in parsed.hostname:
                return False
    return (parsed.scheme == "https" and bool(parsed.hostname)
            and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            and not parsed.hostname.endswith((".invalid", ".test", ".localhost", ".local"))
            and not parsed.username and not parsed.password
            and not any(part in value.lower() for part in ("<", ">", "example.", "placeholder")))


def final_errors(data):
    """Check completeness/consistency; operators must verify the underlying evidence."""
    errors = []
    if not isinstance(data.get("team_number"), int) or isinstance(data.get("team_number"), bool) or not 1 <= data["team_number"] <= 99:
        errors.append("Confirmed team number (1–99) is required.")
    members = data.get("members", [])
    def supplied(value):
        return isinstance(value, str) and bool(value.strip()) and not any(marker in value.lower() for marker in ("pending", "unknown", "tbd"))
    if not isinstance(members, list) or len(members) != 3 or any(
        not isinstance(member, dict) or not supplied(member.get("name")) or not supplied(member.get("student_id"))
        or "<" in member["student_id"] or ">" in member["student_id"] for member in members
    ):
        errors.append("All three confirmed names and student IDs are required; placeholders are not final data.")
    elif len({member["student_id"].strip() for member in members}) != 3:
        errors.append("Student IDs must be distinct.")
    if not public_https(data.get("public_url")):
        errors.append("A real verified public HTTPS URL is required.")
    if data.get("repository") != REPO or data.get("release_url") != REPO + "/releases/tag/v1.0":
        errors.append("Repository and published v1.0 release URLs must match this project.")
    sha = data.get("release_sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha) or sha != data.get("deployed_sha"):
        errors.append("Full release and provider-deployed SHAs must match.")
    if not re.fullmatch(re.escape(REPO) + r"/actions/runs/\d+", str(data.get("main_ci_url", ""))):
        errors.append("A verified green main CI run URL is required.")
    if data.get("scrum_master") != "khuatnhatminhcfpro-cmyk":
        errors.append("Sprint 5 Scrum Master must match the confirmed assignment.")
    if data.get("test_accounts_url") != REPO + "/blob/main/README.md":
        errors.append("Test-account reference must point to the repository README.")
    if not data.get("late_submission_agreement"):
        errors.append("The instructor's actual late-submission arrangement must be recorded.")
    for name in REQUIRED_CONFIRMATIONS:
        if data.get("confirmations", {}).get(name) is not True:
            errors.append(f"Outstanding evidence/confirmation: {name}.")
    return errors


def render_html(data, final=False):
    if final and (errors := final_errors(data)):
        raise ValueError("\n".join(errors))

    def escape(value):
        return html.escape(str(value))

    def link(value, pending):
        return f'<a href="{escape(value)}">{escape(value)}</a>' if value else escape(pending)

    origin = link(data.get("public_url"), "PENDING — actual HTTPS URL not provided/verified")
    number = data.get("team_number")
    team = f"Team {number:02}" if isinstance(number, int) else "Team number pending confirmation"
    people = "<br>".join(escape(member.get("name", "Pending")) + " — " + escape(member.get("student_id") or "student ID pending") for member in data.get("members", []))
    stamp = "" if final else '<p class="draft">DRAFT — NOT READY FOR SUBMISSION</p><p class="notice">Missing data and release checks are pending. No release, public verification, team rehearsal or submission is claimed.</p>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>M5 submission {'FINAL' if final else 'DRAFT'}</title>
<style>@page{{size:A4;margin:20mm;background:white}}html{{background:white}}body{{background:white;font:16px/1.6 Arial,sans-serif;color:#172b4d}}.running{{font-weight:bold;overflow-wrap:anywhere}}h1{{font-size:24px}}.draft{{color:#a12525;font-weight:bold;border:2px solid #a12525;padding:10px}}.notice{{color:#705050}}dt{{font-weight:bold;margin-top:16px}}dd{{margin:4px 0;overflow-wrap:anywhere}}a{{color:#174c8e}}footer{{margin-top:28px;color:#53677f;font-size:12px}}</style></head><body>
<p class="running">Running app: {origin}</p>{stamp}<h1>{escape(team)} — {escape(data.get('product','EduSurvey'))}</h1>
<dl><dt>Members</dt><dd>{people}</dd><dt>Scrum Master (Sprint 5)</dt><dd>@{escape(data.get('scrum_master','Pending'))}</dd>
<dt>Repository</dt><dd>{link(data.get('repository'),'Pending')}</dd><dt>Release v1.0</dt><dd>{link(data.get('release_url'),'PENDING — release not published/verified')}</dd>
<dt>Latest green CI run on main</dt><dd>{link(data.get('main_ci_url'),'Pending')}</dd><dt>Test accounts</dt><dd>{link(data.get('test_accounts_url'),'Pending')} — see the first screen of README.md.</dd></dl>
<footer>{'Final export from operator-confirmed evidence; upload status is tracked separately.' if final else 'CI link is a dated repository observation, not deployed acceptance. Public entry-point update remains #209.'}</footer></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("docs/m5/submission.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/m5"))
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--pdf", action="store_true", help="Print HTML using Playwright Chromium.")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    try:
        content = render_html(data, args.final)
    except ValueError as error:
        parser.exit(2, f"Final export refused:\n{error}\n")
    stem = f"Team{data['team_number']:02}_M5" if args.final else (f"Team{data['team_number']:02}_M5_DRAFT" if isinstance(data.get("team_number"), int) else "M5-submission-DRAFT")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    page_path = args.output_dir / (stem + ".html")
    page_path.write_text(content, encoding="utf-8")
    if args.pdf:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            options = {"headless": True}
            if executable := os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"):
                options["executable_path"] = executable
            browser = playwright.chromium.launch(**options)
            try:
                page = browser.new_page()
                page.goto(page_path.resolve().as_uri())
                page.pdf(path=str(args.output_dir / (stem + ".pdf")), print_background=True, prefer_css_page_size=True, display_header_footer=False)
            finally:
                browser.close()
    print(f"Created {'final export' if args.final else 'explicitly marked draft'} in {args.output_dir}. Not uploaded or submitted.")


if __name__ == "__main__":
    main()
