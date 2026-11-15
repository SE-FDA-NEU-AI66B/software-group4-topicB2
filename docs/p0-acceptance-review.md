# P0 Acceptance Contract Review (#188)

Review baseline: `origin/main` at `5a52af6`, inspected 2026-11-15. Related stories: US01 #14, US02 #18, US03 #22, US04 #50 and US11 #183. This document separates current observations, proposed decisions, future acceptance tests and actual evidence. No production behavior is changed by this review.

## Comparison and proposed decisions

PO: Khuat Dinh Trung (`@khuatnhatminhcfpro-cmyk`). **PO review status: APPROVED on 2026-11-15 by Khuat Dinh Trung in the explicit task-review response.** D01/D02/D03/D04 and the inclusive visible-outcome interpretation in D06 were approved. The PO explicitly deferred copied-cookie revocation and deployed/browser timing evidence; D05 is not an accepted risk or completed requirement. Approval authorizes this documented target/normalization, not an authentication rewrite in this PR.

| ID / checked scope | Required behavior / source | Observed implementation | Recommended decision | Approval / implementation |
|---|---|---|---|---|
| D01: US01 #14, invalid credentials | `docs/requirements.md` US01 and `docs/design.md`: exact message `Invalid email or password.` | `src/app.py::login`: 401 / INVALID_CREDENTIALS with `Email or password is incorrect.`. **The inspected JS handler already selects the required message** for 401 in `src/static/js/login.js`; this is an API/design discrepancy, not proof that browser wording is wrong. | Keep the requirement's exact text; align the future API error message too. Preserve status, code, generic wrong-password/unknown-email response and account privacy. | PO APPROVED; implementation pending #214. |
| D02: US02 #18, status spelling | Baseline requirements said `Due Soon`; story #18, UI documentation and implementation use `Due soon`. The spelling is normalized here after approval. | `src/app.py::get_student_evaluations`, `src/status.py`, JS counters/filters/cards and existing boundary tests consistently use `Due soon`. | Canonicalize the documentation to `Due soon` after explicit PO approval. Do not rename the API/UI label or change the strict <24h threshold. At exactly 24h it remains Active; expiry equality remains Closed. | PO APPROVED; requirements spelling normalized in this PR; runtime unchanged. |
| D03: US03 #22, duplicate message | Requirements: `You have already completed this evaluation.` | Questions and submission endpoints return 409 / DUPLICATE_SUBMISSION with `You have already submitted this evaluation.`. `complete_evaluation.js` displays the API error message directly. | Keep the requirement's exact text as the future user/API message on both endpoints. Preserve 409, code, one-response rule and existing saved answers. | PO APPROVED; implementation pending #214. |
| D04: US11 #183, browser logout/navigation | Requirements: sign out and redirect to login; later protected-page access also redirects to login. | `POST /api/auth/logout` clears the current session and returns 200 JSON `{authenticated:false}`. `login_required` returns 401 JSON even for protected HTML pages. Templates/scripts have no working logout control. | Keep API logout 200 JSON and anonymous API access 401 JSON. Add a browser logout action that calls the API then navigates to `/login`; unauthenticated HTML page requests redirect to `/login`. Wrong-role authenticated access remains 403. Future implementation must distinguish HTML routes from APIs. | PO APPROVED; HTML redirect backend pending #215; browser work #201/#202. |
| D05: US11 #183, meaning of session invalidation | Requirements say the previous session must not allow protected functions after logout. They do not define copied signed-cookie replay or a server-side session store. | Flask's default signed client cookie is cleared in the current browser by `session.clear()`; no explicit server-side revocation store/version is present. Clearing one client's cookie is not evidence that a saved cookie is revoked. | Test current-client logout and copied-cookie replay separately. Keep replay revocation an unresolved security/design decision; do not accept the risk or promise a fix implicitly. A separate review must decide whether revocation is required and select a compatible design. | DEFERRED by PO; design review #216; no revocation pass claimed. |
| D06: P0 timing, US01/US03/US04/US11 and BR8 | Requirements say within 3 seconds under normal conditions but do not specify interval, clock, load or equality. | Existing functional tests assert statuses/data; whole-suite elapsed time measures many tests/setup steps, not a user interaction. | Use the approved inclusive budget **duration <=3,000ms**, with 2,999/3,000/3,001ms classified pass/pass/fail. Browser acceptance runs from user action to usable/visible outcome, including required navigation. Local Flask timings are diagnostic components only, not proof of browser/deployed acceptance. | PO APPROVED for inclusive visible-outcome budget; exact deployment/browser profile and measured acceptance remain pending #205/#206/#210. |

The lecturer permission message is already consistent in requirements, API and page checks: `You do not have permission to view this course feedback.`. Keep its existing US04 regression assertions and do not change the permission rule.

## Measurement contract

Two measurements must never be substituted for each other:

- **Local diagnostic:** time immediately before a Flask test-client request until the response body has been consumed, using monotonic `time.perf_counter_ns`. Database preparation, password hashing for seeding, pre-authentication/session setup, cleanup and verification are excluded. It includes request dispatch, password verification for login, SQL and response generation. It excludes HTTP transport/TLS, browser JavaScript, DOM readiness and redirect-driven page loading. Use an isolated temporary SQLite database, fixed application time, one process, sequential requests, three warm-ups and thirty measured samples per operation. Record every raw duration, status, maximum/p50/p95, environment/dependency versions, data volume and source fingerprint; no credentials or cookie values in the report.
- **Browser/deployment acceptance (future):** use a monotonic browser clock from the triggering click/submit until the outcome below is visibly usable. For logout, require the login page plus subsequent protected-access denial; for login include the final role landing page. Record deployed commit/URL, OS/browser/device, network conditions, platform warm/cold state and any concurrent load. Proposed normal profile is one foreground user, warm service, no background batch load, three warm-ups and thirty samples. Every measured normal sample must meet the inclusive budget; p95/max are reported, not used to hide a slow sample. Cold starts are reported separately under the M5 allowance, never silently mixed/excluded. The exact host/device/network profile must be agreed and recorded before claiming BR8 acceptance.

| Interaction | Start -> visible outcome for future browser evidence | Owner / dependency |
|---|---|---|
| US01 login | Submit valid credentials -> final role page ready | Duc Anh / Trung, #201 and #210 |
| US02 list | Select My Evaluations -> cards/empty state ready | Trung, #201 / #210; list timing is a proposed P0 extension to BR8, not a separately quoted US02 3s criterion |
| US03 open questions | Click Start Evaluation -> all questions/controls ready | Trung / Duc Anh, #201 / #210 |
| US03 submit | Confirm valid answers -> saved-submission confirmation visible | Duc Anh / Trung, #201 / #210 |
| US04 feedback | Select assigned feedback -> ratings/comments/count visible | Trung / Duc Anh, #202 / #210 |
| US11 logout | Click Sign out -> login page usable; protected follow-up denied | Trung, #201/#202; #186 for current-client API checks |

No production service, transport profile or browser run is assumed to exist yet. Instrumentation under #206 and deployment under #205 precede the final browser measurements. Do not change runtime authentication, reduce password hashing, loosen deadlines or skip validation to improve timing.

## Target test register

At the original review baseline, all target assertions below were **NOT IMPLEMENTED / NOT RUN**. Integration update after #218: **P0C-03, P0C-04 and P0C-07 are now implemented** in `tests/test_p0_browser_contracts.py` and verified through real local Chromium; see [the current browser mappings and results](testing.md). These functional checks do not establish deployed timing, server HTML redirects or cookie replay revocation. All remaining target assertions below retain their pending status. P0C-01/02 name existing functional nodes whose current message expectations must be updated in a future implementation PR; other named functions remain proposed except the three implemented browser nodes identified above. Reuse those existing credential cases rather than duplicate them. Select browser tooling in a separate implementation task; a proposed browser file does not imply a dependency is installed. Fixed-time and SQLite isolation apply to functional tests; real latency uses the monotonic performance clock, not a mocked duration asserted as observed speed.

| New ID | Proposed exact pytest node | Expected behavior after approval | Owner / dependency |
|---|---|---|---|
| P0C-01 | `tests/test_auth.py::test_login_wrong_password` (existing node; target assertion pending) | 401 / INVALID_CREDENTIALS and exact `Invalid email or password.`; no authenticated session | Duc Anh; #214 |
| P0C-02 | `tests/test_auth.py::test_login_unknown_email` (existing node; target assertion pending) | Same response as P0C-01; no email enumeration | Duc Anh; #214 |
| P0C-03 | `tests/test_p0_browser_contracts.py::test_login_error_visible_message` | Wrong credentials visibly show exact required message | Trung; implemented by #201 / merged #218; current mapping in testing.md |
| P0C-04 | `tests/test_p0_browser_contracts.py::test_due_soon_label_and_filter` | API/card/filter/counter use `Due soon`; existing 24h API boundary tests remain | Trung; approved D02 / #201 |
| P0C-05 | `tests/test_submission_workflow.py::test_duplicate_submission_canonical_message` | 409 / DUPLICATE_SUBMISSION and exact required completed message; saved response/answers unchanged | Duc Anh; #214 |
| P0C-06 | `tests/test_submission_workflow.py::test_duplicate_questions_canonical_message` | Reopening a submitted evaluation's questions returns matching 409/code/message | Duc Anh; #214 |
| P0C-07 | `tests/test_p0_browser_contracts.py::test_logout_navigates_to_login` | Visible logout calls API then reaches usable `/login`; later protected access denied | Trung; approved D04 / #201/#202 |
| P0C-08 | `tests/test_auth.py::test_protected_html_redirects_after_logout` | 302 with Location resolving to `/login` for protected HTML after logout; followed page 200; API assertions remain 401 JSON | Duc Anh; #215; change only HTML expectations in future PR |
| P0C-09 | `tests/test_auth.py::test_saved_cookie_rejected_after_logout` | Copied cookie denied only **if revocation is adopted**; target/protocol unresolved, do not enforce/claim pass yet | Sy Huy + Duc Anh; #216, D05 target still unresolved |
| P0C-10 | `tests/test_p0_latency.py::test_latency_budget_boundaries[2999]` | Budget classifier accepts 2,999ms; synthetic limit test, not real performance evidence | Duc Anh; approved D06 / #210 |
| P0C-11 | `tests/test_p0_latency.py::test_latency_budget_boundaries[3000]` | Accepts equality at 3,000ms | Duc Anh; approved D06 / #210 |
| P0C-12 | `tests/test_p0_latency.py::test_latency_budget_boundaries[3001]` | Rejects 3,001ms | Duc Anh; approved D06 / #210 |
| P0C-13 | `tests/test_p0_browser_latency.py::test_visible_p0_latency[login]` | Real login visible-outcome measurement <=3,000ms under the agreed profile; every sample validated | Duc Anh + Trung; #205/#206/#210 and approved D06 |
| P0C-14 | `tests/test_p0_browser_latency.py::test_visible_p0_latency[list]` | Real list visible-outcome measurement <=3,000ms under the agreed profile; every sample validated | Duc Anh + Trung; #205/#206/#210 and approved D06 |
| P0C-15 | `tests/test_p0_browser_latency.py::test_visible_p0_latency[questions]` | Real questions visible-outcome measurement <=3,000ms under the agreed profile; every sample validated | Duc Anh + Trung; #205/#206/#210 and approved D06 |
| P0C-16 | `tests/test_p0_browser_latency.py::test_visible_p0_latency[submission]` | Real submission visible-outcome measurement <=3,000ms under the agreed profile; every sample validated | Duc Anh + Trung; #205/#206/#210 and approved D06 |
| P0C-17 | `tests/test_p0_browser_latency.py::test_visible_p0_latency[feedback]` | Real feedback visible-outcome measurement <=3,000ms under the agreed profile; every sample validated | Duc Anh + Trung; #205/#206/#210 and approved D06 |
| P0C-18 | `tests/test_p0_browser_latency.py::test_visible_p0_latency[logout]` | Real logout visible-outcome measurement <=3,000ms under the agreed profile; every sample validated | Duc Anh + Trung; #205/#206/#210 and approved D06 |

Existing tests remain authoritative for current behavior until a separate approved implementation PR updates specific expectations. Current logout/session tests, duplicate immutability tests and all existing US02 boundaries must be retained. The new cases above do not replace unrelated NOT IMPLEMENTED rows in testing.md.

## Evidence and review completion

Actual command (exit 0):

```bash
python tools/measure_p0_latency.py --samples 30 --warmups 3 --output docs/evidence/p0-local-latency.json
```

Raw durations, dependency/OS/CPU metadata and source/script fingerprints are retained in [p0-local-latency.json](evidence/p0-local-latency.json). To reproduce, install requirements-dev.txt; the diagnostic uses only its application dependencies plus the Python standard library. No server or production database is needed. Numerical durations vary by machine/run; do not overwrite this dated evidence and claim it is the original run.

| Operation | Samples after warm-up | p50 ms | p95 ms | Maximum ms | Observed HTTP |
|---|---:|---:|---:|---:|---|
| login | 30 | 60.252 | 65.182 | 74.855 | 200 |
| list | 30 | 0.346 | 0.434 | 0.761 | 200 |
| questions | 30 | 0.331 | 0.726 | 0.734 | 200 |
| submission | 30 | 0.799 | 2.237 | 2.750 | 201 |
| feedback_api | 30 | 0.666 | 0.731 | 0.987 | 200 |
| feedback_html | 30 | 0.914 | 1.075 | 1.409 | 200 |
| logout | 30 | 0.143 | 0.169 | 0.187 | 200 |

All local samples are below the 3,000ms reference, **but browser/deployed acceptance is NOT EVALUATED**. Login role navigation, JavaScript rendering, network latency and the required browser logout path were not measured. The recorded environment is Darwin 23.6.0, arm64, Python 3.12.4, Flask 3.0.3, Werkzeug 3.0.3, SQLite 3.45.3. This is single-process sequential local data, not load/capacity evidence.

Controlled copied-cookie observation: current client `/api/auth/me` after logout returned **401**; a second isolated client replaying the copied pre-logout cookie returned **200**. This confirms that the observed current-client logout does not revoke that saved cookie. No token/cookie/password is exported. This is a real unresolved finding under #216, not a passing revocation regression test or an approved risk acceptance.

Functional baseline on this branch: `python -m pytest -v` -> **106 passed in 2.83s**. Tests and production source remain unchanged; this result is separate from request latency. #187 was an unmerged independent test PR when this baseline was captured and is not included in this measurement-time count.

Additional navigation evidence is source/route inspection only: login.js sends lecturer/admin users to `/lecturer` and `/admin`, while those exact routes are not registered on this baseline (the lecturer pages are `/lecturer/feedback` and its detail). The submission JS still has a stale comment about non-persistence and a generic confirmation, despite the tested server persisting responses. #201/#202/#210 must resolve/verify usable role landings and visible completion before browser timing acceptance. No browser run or redirect pass is claimed here.

Execution dependencies and single responsible owners:

- #214: Duc Anh, 2h, future login/duplicate API message alignment; reuses credential tests and preserves statuses, rules and saved data.
- #215: Duc Anh, 2h, future protected-HTML redirects; keeps API 200/401 JSON and wrong-role 403.
- #216: Sy Huy, 3h, revocation policy/design review with Duc Anh and PO; target acceptance remains pending.
- #201/#202: Trung, browser controls/navigation and visible error text; dependent on the agreed backend contract.
- #205/#206/#210: deployment/instrumentation and real browser evidence; no final host/device/network acceptance profile is fabricated.

The review/planning work is ready for independent review: five contract discrepancies are documented, PO decisions are explicit, exact future test IDs/nodes and owner/dependencies exist, and local evidence is reproducible. Runtime implementation, revocation policy and deployed timing remain visibly pending in their own tasks; closing the review issue does not close those implementation/security criteria.

## Integration with merged M5 UI

Main `2b644c7` includes #213 and #218. The source-only navigation findings above describe the original diagnostic baseline: #218 has since corrected role landings, added persisted submission receipts and visible logout navigation. P0C-03/04/07 now have real browser nodes. Preserve the original latency samples and copied-cookie observation as dated evidence; no measurement is silently regenerated, and #214/#215/#216 plus deployment timing remain separate.

## Backend contract implementation update

After the backend audit, P0C-01/02 (canonical credential messages), P0C-05/06 (canonical duplicate messages with data preserved), and P0C-08 (HTML-only redirects, API JSON unchanged) are implemented and mapped in [testing.md](testing.md). Earlier baseline diagnostics and future-register status text are historical; the current verification register supersedes those pending markers for these five IDs. P0C-09 copied-cookie policy and all deployed timing assertions remain pending. The backend runtime/health/backup additions are documented separately in [backend.md](backend.md).
