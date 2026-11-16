# Pre-submission M5 project audit

Date: 2026-11-16 (Asia/Ho_Chi_Minh). Base main: `b26dfc8`.
Scope: all existing Python/backend/database/runtime/deploy-tool/submission-pack
checks, browser workflows and source review, with priority on US01/02/03/04/11.
This is local regression evidence; it is not final public-release sign-off.

## Confirmed defects and fixes

| Finding | Correction | Regression evidence |
|---|---|---|
| US02 joined one evaluation to every course lecturer, duplicating cards and totals | Use the same deterministic primary lecturer (lowest assigned user ID) as the questions endpoint; one row per evaluation | M5-A01 |
| A submitted response lost its visible saved receipt after closure/expiry, although the list still said Completed | Check the student's submitted response after enrollment authorization and before closed/deadline checks on questions GET; return the existing canonical duplicate 409 so the UI restores its receipt. New submissions remain blocked. | M5-A02/A04 |
| Two tabs could both pass the duplicate check, then produce a 503 on the unique constraint or replace a previously read draft | Reserve SQLite writer with BEGIN IMMEDIATE before evaluation/duplicate reads and writes. The competing tab sees the committed response and returns canonical 409. Existing atomic rollback remains. | M5-A03, new and draft variants |
| Topic classifiers treated fragments in “examples”, “latest” and “contest” as exam/test keywords | Match word boundaries, with ordinary plural suffixes; retain existing topic scoring/priority | M5-A05; optional US05, separate from P0 acceptance |

The BR9 status label is also aligned to the already approved canonical “Due soon” wording.

No schema migration or data reset is required. SQLite still has a five-second
lock timeout; persistent overload can still return a retryable 503. The change
serializes submission writes, not general horizontal scaling. Selecting one
lecturer preserves the existing singular display contract; team teaching does
not multiply evaluations.

## Five P0 checks

| Story | Existing coverage retained and actual verification |
|---|---|
| US01 | Valid/invalid credentials, unknown email, roles, session and protected access; real student/lecturer login via visible controls |
| US02 | Enrollment separation, empty state, all statuses, strict 24-hour boundary below/at/above, exactly three active example; new team-teaching regression |
| US03 | Required-answer/rating/text boundaries, deadline/closed/duplicate/enrollment rejection, transaction/persistence; new simultaneous-tab and expired-receipt checks |
| US04 | Submitted-only comments/ratings/counts, assigned-course restrictions, wrong-role/anonymous denial, useful error/empty states; new browser flow reads the actual student submission as lecturer |
| US11 | Visible and keyboard sign-out for roles, session cleared, anonymous/idempotent logout and subsequent protected API denial; copied-cookie revocation remains the separate unresolved #216 policy |

The cross-role browser check uses click navigation and keyboard rating selection
at 1440×900 and 390×844. It submits a response, closes/expires the evaluation,
reloads the saved receipt, signs out, logs in as lecturer, sees exactly one
completed response/rating/comment, signs out and receives 401 on the feedback
API. Screenshots use synthetic data: [phone](evidence/m5-preflight/cross-role-390.png),
[laptop](evidence/m5-preflight/cross-role-1440.png). These are viewport checks,
not a physical-phone/public-network test or a full accessibility audit.

## Actual results and reproduction

- Authorized baseline: **278 passed in 79.57s**.
- Final suite: **286 passed in 87.53s**, zero failures/errors/skips; **91% src coverage**.
- Ruff and `git diff --check`: passed.
- Real local production-mode Gunicorn: temporary M5 demo DB, healthy `/health`,
  successful login/list, Secure/HttpOnly/SameSite cookie attributes verified.
  No existing development or production database was changed.

[JUnit](evidence/m5-preflight/pytest.xml),
[coverage/results](evidence/m5-preflight/pytest-summary.txt),
[source hashes, environment and repository state](evidence/m5-preflight/audit.json),
[Gunicorn evidence](evidence/m5-preflight/gunicorn-smoke.json) are retained.
The initial restricted run could not bind localhost. The corrected authorized
baseline passed. New red captures establish the P0 and keyword defects. The
first cross-role test needed a keyboard locator correction for a label-covered
radio; final checks do not skip it. Python 3.14 reports SQLite-handle
ResourceWarnings in test fixtures; these remain visible in run provenance.

```bash
python -m pip install -r requirements-dev.txt -r requirements-prod.txt
python -m playwright install chromium
python -m pytest -q --cov=src --cov-report=term-missing --junitxml=junit.xml
ruff check .
git diff --check
```

This local run used the existing isolated venv and
`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
Source hashes pin the tested changes; CI must independently pass the PR commit.

## Still required before final M5 submission

| Unverified release item | Next action / owner |
|---|---|
| Public HTTPS URL, provider SHA and durable mount | Đức Anh/Huy: supply actual host access; verify private-desktop/physical-phone P0 and restart persistence under #205/#210. Repo homepage is null and deployment records empty; this does not rule out an unreported service. |
| Required green checks on main | Repository admin: apply/read back the prepared named-check rules; current effective rules only enforce PR/approval and deletion/force-push restrictions (#207). Current actor has no admin permission. |
| Hosted logs/monitoring, off-host backup and rollback | Đức Anh/Huy: perform and retain real platform checks; local tools/tests do not prove scheduled operations (#204/#206/#208). |
| <=3,000ms user-action-to-visible outcome | Measure on the real deployment with environment/load/clock documented; pytest duration and server timings are insufficient (#188/#210). |
| v1.0 identity and final PDF | Trung/team: verified deployed SHA must match release SHA; confirm student IDs, real rehearsal and submission arrangements; no release currently observed (#211). |
| Handover/SM review and instructor section-count clarification | Complete real external confirmations and contribution evidence; retain pending status instead of inventing approval (#208/#212). |

AI assistance: Codex — code review, fixes and test execution.
