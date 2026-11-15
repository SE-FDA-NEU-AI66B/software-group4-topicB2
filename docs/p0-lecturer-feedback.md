# Lecturer P0 navigation and error UX — #202

Related story: US04 #50; coordination #200; approved contract review #188 / #217. Branch `feature/202-lecturer-feedback-ux` starts at main `2cb2b05` and reuses #201's role landing, account navigation, shared sign-out control and browser fixtures.

## Behavior and contracts

From `/`, sign in as a lecturer, choose **Review feedback**, inspect completed counts, average/individual ratings and written comments, return through **All evaluations**, and use **Sign out**. No normal step requires another typed URL. Existing SQL ownership and `status='submitted'` filtering are unchanged: draft responses are excluded from the list counts and detail output, and other lecturers' course feedback is never exposed.

The existing `lecturer_feedback.html` and `/lecturer/feedback` list/detail routes remain the implementation. Styling is extracted into `static/css/lecturer_feedback.css` and aligned with the student workspace. The page has a keyboard skip link, meaningful link names for repeated Review feedback controls, visible focus, wrapping long text, and responsive stacked phone layouts. Shared session controls remain visible on list, detail, empty and signed-in error pages.

| Situation | Visible explanation and next action | HTTP behavior |
|---|---|---|
| No assigned evaluations | Explains missing assignments/evaluations; refresh assigned list or contact university administrator | 200 |
| Assigned evaluation with no submissions | Explains that only completed submissions appear, drafts are excluded; refresh feedback | 200, count 0 |
| Completed responses without ratings/comments | Explains which answer type is absent; return to All evaluations or wait for further submissions | 200 |
| Existing evaluation in an unassigned course | Exact message: `You do not have permission to view this course feedback.`; explains assignment requirement; return to assigned evaluations | 403, no course title/feedback disclosed |
| Removed/nonexistent evaluation | `Evaluation not found.`; explains outdated link/removal; return to assigned evaluations | 404 |
| Anonymous browser | Explains missing/ended session; visible Sign in to continue | 401 HTML, **not a redirect** |
| Wrong-role browser | Explains lecturer role requirement; My account and shared Sign out provide recovery | 403 HTML |
| SQLite cannot load feedback | Safe temporary-unavailability explanation and Try again; internal exception is logged server-side, not sent to the page | 503 HTML |

A small response wrapper applies only to the two lecturer HTML routes. An explicit HTML Accept preference receives an HTML error; JSON/no-Accept requests preserve the existing JSON 401/403 contracts. MIME negotiation uses supported HTML/JSON types rather than the first MIME entry, because Chrome can prefer an unsupported signed-exchange type. API routes are unchanged, always retain their current JSON/status behavior, and all lecturer page responses are `Cache-Control: no-store`. The wrapper does not change authentication, revoke saved cookies or implement #215's future HTML redirect policy.

## Automated case IDs and node mapping

All nodes below are in `tests/test_p0_browser_contracts.py`. The shared fixture uses the existing temporary SQLite schema, controlled application time `2026-11-04T12:00:00`, a real loopback Werkzeug server on a random port, and fresh Chromium contexts. Synthetic data includes one assigned submitted response, a draft comment and a foreign-course submitted response. No production database or manually running server is used.

| Case ID | Actual pytest node / parameter variants | Assertions |
|---|---|---|
| M5-L01, M5-L02 / P0C-07 | `test_lecturer_feedback_click_through[laptop]`, `[phone]` | Home → real login → assigned-only list/count → keyboard review → rating 4/5, average 4.0/5, written comment, completed count 1 → reload → back → keyboard logout → login; follow-up page/API 401. Draft and foreign comments excluded; long unbroken/HTML-like comments remain escaped text without horizontal overflow. |
| M5-L03 | `test_lecturer_feedback_empty_states` | No submitted responses gives count 0 and useful refresh; deleting assignments yields distinct no-evaluations state with recovery guidance. |
| M5-L04 | `test_lecturer_feedback_access_error_recovery[/lecturer/feedback/2-403]`, `[/lecturer/feedback/999-404]` | Exact permission/not-found messages and correct statuses; foreign course title/comment absent; recovery link returns to usable assigned list. |
| M5-L05 | `test_lecturer_feedback_wrong_role_browser_errors[anonymous]`, `[student]`, `[administrator]` | Browser HTML 401/403 without feedback disclosure; working sign-in/account links; API and explicitly JSON page requests still return JSON denials. Phone view does not overflow. |
| M5-L06 | `test_lecturer_feedback_unavailable_retry` | Real injected SQLite OperationalError gives safe 503; private exception detail/feedback absent; restoring DB and clicking Try again recovers. |

Existing lecturer page/API ownership/filtering tests, authentication cases, all US02 strict 24-hour/deadline cases, and student browser checks remain unchanged.

## Reproduce and actual results

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
# Linux: python -m playwright install --with-deps chromium
python -m pytest -q
python -m pytest -q tests/test_p0_browser_contracts.py -k lecturer_feedback
python tools/run_student_demo.py
```

Open `http://127.0.0.1:5000/` in a fresh browser context. Use documented seeded `lecturer1@edusurvey.edu` / `Password123!`. Select **Review feedback: Artificial Intelligence Mid-Semester Evaluation** for submitted ratings/comments/count 1, then return and inspect **Software Engineering Mid-Semester Evaluation** for an empty submitted-feedback state in this disposable demo. The demo tool removes the first student's old response in that evaluation for the student walkthrough. Data survives navigation while the process runs and is removed on Ctrl+C; the tool never writes `data/edusurvey.db`.

Actual local verification on 2026-11-15: macOS arm64, Python 3.14.8, Flask 3.1.2, Playwright 1.65.2, Google Chrome 157.0.8103.78. Headless contexts: laptop 1440×900 and phone 390×844.

```text
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
P0_SCREENSHOT_DIR=/private/tmp/p0-202-screenshots python -m pytest -q
125 passed in 49.21s

python -m pytest -q tests/test_lecturer_feedback.py
8 passed in 0.08s
```

There are **116 retained tests + 9 new browser variants**, with no skips. The full run precedes a recovery-copy-only clarification for absent rating/written answers; the unchanged lecturer suite was rerun afterward, and CI validates the final tree. Ruff on the changed test module passes; existing app lint findings are outside this UI change. These durations are suite execution time, **not acceptance latency evidence**.

A separate walkthrough used the documented seeded lecturer account on the disposable launcher in fresh laptop and phone contexts. Both passed: login → submitted AI feedback/count 1 → empty Software Engineering feedback → intentional unassigned evaluation 403 with exact message and recovery → logout/login → protected API 401. Screenshot of that denial uses the seeded demo; other screenshots use isolated synthetic pytest data.

Screenshots were generated by real Chrome interactions and visually inspected:

- [Laptop feedback detail](evidence/202/detail-laptop.png)
- [Phone feedback detail](evidence/202/detail-phone.png)
- [Phone assignment empty state](evidence/202/empty-phone.png)
- [Phone unassigned-course denial](evidence/202/denied-phone.png)

Initial validation caught three integration issues, all corrected without skips: a markup-sensitive existing completed-count assertion (preserved the original `<strong>` markup), a new test navigating before login finished (wait for role landing), and HTML negotiation treating Chrome's signed-exchange MIME as the desired response type (match the supported types). The final full run above passes; historical evidence is not rewritten.

## Pending public evidence and review

No public deployment URL is documented in the repository at verification time. Fresh local Chrome contexts and responsive viewports establish local behavior, not physical-phone/public-HTTPS or Safari/Firefox acceptance. Durable deployment/demo data and public mobile/private-desktop checks remain #204/#205/#210; the deployed ≤3,000ms criterion remains pending. This task records no copied-cookie revocation (#216), canonical backend message changes (#214), anonymous HTML redirects (#215) or measured public performance pass. Teammate approval and green CI are required before merge; no automatic self-merge or self-approval.
