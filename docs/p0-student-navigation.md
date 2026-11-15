# Student P0 navigation verification — #201

Implemented on branch `feature/201-student-p0-navigation`, based on main `5a52af6`. Related stories: US01 #14, US02 #18, US03 #22 and US11 #183; M5 coordination #200. The approved #188 contract decisions are recorded in [PR #217](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/217). That documentation PR is still separate; this UI change does not require its merge to run.

## Click-through and roles

Start at `/` or `/login`. Expand “Try a demo account” for seeded credentials, sign in, select **Start Evaluation**, answer the required questions, review and submit, then select **Back to My Evaluations**. The list shows **Completed**, including after a page reload. **My account** and **Sign out** are visible on student list/question pages and existing lecturer feedback pages. The keyboard can activate rating choices, dialogs and logout.

Students land on `/evaluations`, lecturers on the existing `/lecturer/feedback`, and administrators on a protected `/account` page explaining the available demo scope. The administrator page intentionally offers no P1 management tools. Server-side role/enrollment, required-answer, closed/deadline, duplicate and strict `<24h` rules are preserved.

Submission success requires the actual API `201` response with `status=submitted`. The page locks further submission and presents a saved receipt. Reloading that completed evaluation uses the server's duplicate result to display “You have already completed this evaluation.” rather than an open form or generic failure. Deadline/enrollment/closed errors retain a visible route back to the list and an explanation/next action. A network failure during logout leaves an actionable retry.

## Reproduce locally

Install runtime dependencies as in SETUP.md and run:

```bash
python tools/run_student_demo.py
```

Open `http://127.0.0.1:5000/` in a fresh browser context. Use `student1@edusurvey.edu` and shared demo password `Password123!`; lecturer `lecturer1@edusurvey.edu` and administrator `admin@edusurvey.edu` use the same seeded password. These are public synthetic demo accounts. The disposable launcher creates a fresh temporary SQLite database and makes the first enrolled evaluation available with a deadline seven days ahead. Data survives reloads within that process, then is removed on exit. It does not initialize/overwrite the working database. This is needed because the original fixed-date seed's open evaluation deadlines are historical; durable deployment demo data remains #204's responsibility.

For automated checks:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest -q tests/test_p0_browser_contracts.py
python -m pytest -q
```

Linux browser dependencies: `python -m playwright install --with-deps chromium`. CI installs them and includes browser cases in its existing pytest job; no separate manually started server is needed. The tests use `api_client`'s temporary SQLite schema/data, patched application clock `2026-11-04T12:00:00`, a loopback Werkzeug server on an ephemeral port, and a fresh Chromium context per case. They never read production data. Login-message mapping uses an intercepted API rejection, preserving the existing API wrong-password/unknown-email partition tests.

## Actual evidence (2026-11-15)

Local environment: macOS arm64, Python 3.14.8, Flask 3.1.2, Playwright 1.65.2 and Google Chrome 157.0.8103.78. Headless viewport sizes: phone **390×844**, laptop **1440×900**. Evidence is from local browser interactions, not a public deployment or physical mobile device.

Executed using an isolated temporary virtual environment:

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
P0_SCREENSHOT_DIR=/private/tmp/p0-201-screenshots \
python -m pytest -q --cov --cov-report=term --junitxml=/private/tmp/201-junit.xml
```

Observed: **115 passed, 214 warnings in 29.67s** (106 existing tests + 9 browser variants; no skipped tests). Python 3.14 reported unclosed SQLite connection ResourceWarnings, including existing fixtures; this run does not establish leak-free resource handling. The new test module and demo launcher pass Ruff; existing `src/app.py` lint findings remain unrelated. JUnit output is temporary local evidence; the CI run is a separate result linked from the PR. Total pytest duration is **not** response-time evidence.

| Checked | Real browser node in `tests/test_p0_browser_contracts.py` | Observation |
|---|---|---|
| Yes — M5-UI01/02, P0C-07 | `test_logout_navigates_to_login[laptop]`, `[phone]` | Home → sign in → assigned list → required-question rejection → keyboard rating/text → review → persisted submission → reload receipt → Completed list → keyboard logout → `/login`; subsequent protected API and HTML requests 401. One saved response and two answers verified directly in temporary SQLite. No horizontal overflow on tested login/list/receipt views. |
| Yes — P0C-03 | `test_login_error_visible_message` | UI displays “Invalid email or password.” with retry guidance; sign-in button remains usable after rejection. |
| Yes — P0C-04 | `test_due_soon_label_and_filter` | Real API data at T+23h59m59s displays Due soon; T+24h displays Active. Due soon filter excludes the Active card. Existing tests retain both-sided boundary coverage. |
| Yes — M5-UI03 | `test_role_landing_and_logout[lecturer@test.com-/lecturer/feedback]`, `[admin@test.com-/account]` | Both non-student roles reach existing pages at phone width, can sign out, and cannot retrieve the student API (403). |
| Yes — M5-UI04 | `test_submission_deadline_race_and_retryable_logout` | Deadline moved to exactly frozen T after opening; server rejects submit without writes. Simulated logout network failure explains recovery; retry reaches login. |
| Yes — M5-UI05 | `test_open_evaluation_error_explains_next_action[closed]`, `[unenrolled]` | Evaluation becomes closed/enrollment removed after list retrieval; questions are rejected, UI gives an explanation and a working Back to evaluations link; no response created. |

The new screenshots are generated by those real tests, use synthetic data and were visually inspected:

- [Saved receipt at phone width](evidence/201/saved-phone.png)
- [Persisted Completed list at laptop width](evidence/201/completed-laptop.png)

A separate Chrome walkthrough also ran against `tools/run_student_demo.py` with the documented seeded student account, both required rating questions, persisted completion and sign-out. Observed result: PASS — two required ratings accepted; Completed count increased from 2 seeded responses to 3, logout reached `/login`, and `/api/auth/me` returned 401 (Chrome 157.0.8103.78). The first ad hoc script incorrectly expected one total completion and failed after submission because the seed already includes two; the fresh-demo rerun used the correct baseline.

## Scope and pending evidence

Browser logout calls the existing JSON logout API and uses `location.replace('/login')` after success. The current session is cleared; protected requests are denied. Authenticated responses and authentication endpoints receive `Cache-Control: no-store`, and restored bfcache pages revalidate the current session. This does not implement server-side copied-cookie revocation (#216), nor the server's future anonymous-HTML redirect contract (#215). This branch's tests explicitly preserve today's anonymous HTML 401 behavior. APIs remain JSON 200/401 and wrong-role access 403. Canonical backend error strings remain #214; the visible UI follows the approved wording.

Public HTTPS deployment, durable seeded data and deployed browser timing evidence depend on #204/#205/#210. No ≤3,000ms SLA, full WCAG audit, screen-reader test, Safari/Firefox support or copied-cookie revocation is claimed from these checks. A teammate's recorded review and green CI are required before merge; this PR must not be self-merged or self-approved.

## Latest main synchronization

2026-11-15: merged main `9e5b647` after refinement PR #191 landed. Both the Sprint 4 pending-case matrix and M5 browser mappings are retained. Reverification with `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python -m pytest -q` returned **115 passed in 31.44s**. This is a local regression result, not deployed timing evidence.
