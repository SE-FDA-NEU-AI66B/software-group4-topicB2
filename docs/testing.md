# EduSurvey M4 Automated Testing

**Latest #207 integration against main `55e81b5`: 257 passed in 76.11s**, zero
failures/errors/skips, on Windows/Python 3.11.9. All 229 main cases plus 28
CI/protection cases are retained. Conflicting introductions and evidence
sections were combined without dropping historical runs; see the final #207
integration section for the exact command and report links.

**Earlier #207 CI verification (2026-11-15): 228 passed in 57.74s**, zero failures,
errors or skips, on Windows/Python 3.11.9. This retains all 200 cases from main
`6acf0dd` and adds 28 CI/protection cases. Whole-repository Ruff passes and is
now blocking in CI. [CI/protection evidence](ci-production-gate.md) distinguishes
the intentionally red, closed rehearsal PR from this green implementation,
the actual current ruleset screenshot and the pending administrator action.

**Latest #204 integration against main `83f76aa` (2026-11-15): 229 passed
in 78.53s, zero failures/errors/skips.** Both sides of the documentation merge
are preserved. Browser tests explicitly wait for fetched questions before
interacting with the form; see the final #204 reconciliation section for the
two initial timing failures, corrections and full rerun evidence.

**Earlier #204 verification (2026-11-15): 216 passed in 58.86s, zero
failures/errors/skips** on Windows/Python 3.11.9. This includes 16 new
production-database cases and all 200 cases from main `6acf0dd`, including the
#205 runtime-contract fixes. The historical #189 FK-OFF/exception-propagation assumptions below
are superseded: current runtime enforces FK=1 and sanitizes SQLite failures as
503/DATABASE_UNAVAILABLE. See the #204 register at the end and
[the database operations runbook](database-operations.md).

**Baseline #190 audit (2026-11-15, main `686bd9e`):** fresh clone + new Python
3.11.9/Windows environment installed `requirements-dev.txt` successfully.
`python -m pytest -v --junitxml=junit.xml` returned **185 passed, 5 failed,
0 skipped**. All **97 story mappings resolve and pass**; failures are additional
runtime/database audit nodes. Runtime FK enforcement from #223 supersedes the
earlier FK-OFF finding, and the old #189 characterization/rollback assumptions
now fail. Historical runs below remain dated evidence. Current baseline CI is
red; current Board access and several substantive reviews remain unresolved.
See [commands, exact failing nodes, CI/review links and sign-off blockers](m4-review-evidence.md)
and [machine-readable mapping check](evidence/190/mapping-audit.json).

### #190 CI remediation after the baseline audit

Both failed Python checks on PR #227 reproduced the same three obsolete #189
assumptions on Linux: [PR run](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43729674333)
and [push run](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43729613376).
The latter reported **3 failed, 187 passed in 45.57s**. This is distinct from
the five-failure Windows baseline archived above.

The user authorized remediation of the failing checks. Production code and CI
gates are unchanged. Real node names and their story dependencies are preserved:

| Retained node / mapping | Updated verification of the #223 runtime contract |
|---|---|
| `tests/test_database_integrity.py::test_runtime_foreign_keys_finding` / DB-189-F01 / US11 #183, US03 #22 | Two independent runtime connections enforce FK=1; orphan insert raises IntegrityError; clean FK check and exact unchanged snapshot |
| `tests/test_database_integrity.py::test_submission_write_failure_rolls_back[new]` / DB-189-07 / US03 #22 | Test-only trigger callback proves answer 2 fails after answer 1 was written; sanitized 503/DATABASE_UNAVAILABLE; exact snapshot rollback; normal retry persists both answers and controlled timestamp |
| `tests/test_database_integrity.py::test_submission_write_failure_rolls_back[draft]` / DB-189-08 / US03 #22 | Same injection/503/retry checks, preserving the original draft response and answers after failure |
| `tests/test_backend_runtime.py::test_production_config_requires_explicit_secrets_and_storage` / BE-05 / #223 | Valid absolute fixture uses tmp_path on each OS; missing/relative storage and missing/short secrets remain rejected |
| `tests/test_backend_runtime.py::test_online_backup_and_restore_round_trip` / BE-07 / #223 | POSIX still requires private mode bits; Windows verifies exposed read/write attributes, without claiming ACL validation. Both platforms execute the entire snapshot/restore/no-overwrite workflow |

No test is skipped, xfailed or removed. `python -m pytest -q
tests/test_database_integrity.py tests/test_backend_runtime.py` returned
**43 passed in 0.95s** on Windows/Python 3.11.9. Changed-module Ruff passed.
The first focused attempt returned 41 passed / 2 failed because its expected
generic 500 was incorrect: SQLite errors have the more specific sanitized
503 handler. The final assertions retain that verified production behavior.

Full local rerun (same Windows/Python 3.11.9 environment, existing Chrome):

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
& .venv/m4-env/Scripts/python.exe -m pytest -v --cov --cov-report=term-missing --junitxml=docs/evidence/190/remediation-pytest.xml
# 190 passed in 51.40s; exit 0; zero failures/errors/skips
```

[Full rerun console](evidence/190/remediation-pytest.txt) and
[JUnit](evidence/190/remediation-pytest.xml) are separate from the unmodified
failing clean-clone baseline. This rerun used the working branch, not a second
fresh environment or an independent human tester. Current PR CI must be read
separately; the historical red-main result is not rewritten.

**Backend audit contract update — 2026-11-15.**

Current behavior supersedes earlier dated 401-HTML/old-message snapshots below: approved #214 uses canonical API messages, and #215 redirects anonymous protected HTML navigation to `/login` while APIs/JSON clients retain JSON 401. Existing denial scenarios and all old test IDs are retained; their HTML-only assertions are deliberately updated. Topic/ranking/statistics APIs now require assigned lecturer access. [Backend file/route map](backend.md) and [runtime handover](backend-runtime.md) explain the implementation and remaining deployment/security limits.


## 1. What we test, and why

Evidence reviewed on 2026-11-15: original M4 documentation (#164), US01 tests (#165), US02 tests (#166 where present), and the team’s US11 work on fetched main `ecc0727`. Integration preserves all original case IDs, the four M4 sections, pending-case markers and historical mutation/run evidence. New verification results below are separate from those historical runs. The later #172/#173 integration adds the already-existing PR lecturer-page routes while preserving main’s shared business functions; unrelated local changes are untouched.

| Layer | What is tested | Technique | Reason / limitations |
|---|---|---|---|
| Services / business logic | Status precedence, deadlines, topic classification; submission validation inside route functions | Unit tests in `test_status.py` and `test_feedback_classifier.py`; equivalence partitions and boundary analysis through API tests | Most business logic remains in `src/app.py`, rather than separate service classes. The standalone status helper and route duplicate logic, so both require coverage. |
| Repository / database | Response and answer uniqueness, submission timestamp storage, queries excluding drafts and unrelated evaluations | In-memory SQLite schema tests; integration tests against `tmp_path` databases | Protects integrity and feedback accuracy. SQL is primarily inline in routes; no general repository abstraction exists. Foreign keys are enabled in schema tests; production `get_db_connection()` does not explicitly enable them, so full runtime FK enforcement is not established. |
| Flask routes / API | Authentication, student role/enrollment, required answers, deadlines, duplicates, lecturer ownership and logout | Flask test client; temporary databases; positive/negative partitions and fixed-time boundary tests where implemented | Exercises request, session, validation and SQL together without starting a server. Successful submission persistence and exact expiry boundaries are now covered by the US03 workflow tests; rating/text numerical boundaries are covered by #184. |
| User interface | HTML roles plus student P0 navigation, persisted completion and visible sign-out | Flask rendering tests and real Playwright Chromium checks at phone/laptop widths | #201 adds 9 browser variants on isolated SQLite and a fixed app clock; see [P0 UI evidence](p0-student-navigation.md). Public deployment timing, full accessibility and copied-cookie revocation remain pending. |

Authentication and authorization receive priority because a role or course-ownership error could expose student feedback. Submission validation, exact deadlines and duplicate prevention protect irreversible response data; database constraints and lecturer filtering provide additional safeguards. A green suite demonstrates only its assertions, not complete acceptance-criteria coverage.

## 2. Test cases for every P0 story

The backlog table and story acceptance criteria in [requirements.md](requirements.md) confirm exactly five P0 stories: **US01 User Login and Authentication; US02 View Available Course Evaluations; US03 Complete and Submit Course Evaluation; US04 Review Submitted Student Feedback; US11 User Sign Out**.

Inputs below describe the implementation contract. HTTP errors use `error.code` and `error.message`. Messages shown are verified from source; an existing test may assert only the status/code, as detailed in Section 3. A pending case is a specification derived from source, not execution evidence.

For new tests, use a separate temporary SQLite database per case, load `src/schema.sql`, seed an enrolled student and assigned lecturer, and freeze `src.app.datetime` at T=2026-11-03T12:00:00 unless another instant is specified. Fresh submissions must have no pre-existing submitted response; delete answers before deleting the seeded response. Never initialize or read `data/edusurvey.db`. Existing tests retain their own fixtures and time limitations described in Section 3.

| ID | Story | Input | Expected result | Kind |
|---|---|---|---|---|
| TC-01 | US01 | POST /api/auth/login; student1@edusurvey.edu / Password123! | 200; authenticated=true; student role; no password_hash | Normal |
| TC-02 | US01 | Same email; password=wrong-password | 401; INVALID_CREDENTIALS; "Invalid email or password." | Error |
| TC-03 | US01 | unknown@edusurvey.edu / Password123! | 401; INVALID_CREDENTIALS | Error |
| TC-04 | US01 | Known email; omit password | 400; MISSING_CREDENTIALS; "Email and password are required." | Error |
| TC-05 | US02 | Student 1 enrolled in course 1; GET /api/evaluations; three open/closed evaluations | 200; count=3; Course Feedback has title, course, lecturer, deadline and Active status | Normal |
| TC-06 | US02 | Anonymous GET /api/evaluations | 401; UNAUTHORIZED | Error |
| TC-07 | US02 | Lecturer GET /api/evaluations | 403; FORBIDDEN | Error |
| TC-08 | US02 | Student 1; T=2026-11-03T12:00:00; deadline=T+23h59m59s | 200; Due soon | Boundary |
| TC-09 | US02 | Same T; deadline=T+24h | 200; Active | Boundary |
| TC-10 | US02 | Same T; deadline=T+24h1s | 200; Active | Boundary |
| TC-11 | US02 | Same T; open evaluation; deadline=T-1s | 200; Closed | Boundary |
| TC-12 | US02 | Same T; open evaluation; deadline=T | 200; Closed | Boundary |
| TC-13 | US02 | Same T; open evaluation; deadline=T+1s | 200; Due soon | Boundary |
| TC-14 | US03 | Fresh enrolled student; rating question 1=5 and required text question 2="The course is useful."; frozen T; open evaluation | 201; status=submitted; one response and answer persisted; "Evaluation submitted successfully." | Normal |
| TC-15 | US03 | Student session; POST /api/submissions with evaluation_id=1, answers={} | 400; MISSING_REQUIRED_ANSWERS; "Please answer all required questions before submitting." | Error |
| TC-16 | US03 | Existing submitted response for student 1/evaluation 1; valid_payload() | 409; DUPLICATE_SUBMISSION; "You have already completed this evaluation." | Error |
| TC-17 | US03 | Anonymous; valid submission payload | 401; UNAUTHORIZED | Error |
| TC-18 | US03 | Frozen T=2026-11-04T12:00:00; deadline=T+1s; valid answers and no response | 201; status=submitted | Boundary |
| TC-19 | US03 | Same frozen T; deadline=T; valid answers and no response | 400; DEADLINE_EXPIRED; "The submission deadline has passed." | Boundary |
| TC-20 | US03 | Same frozen T; deadline=T-1s; valid answers and no response | 400; DEADLINE_EXPIRED; "The submission deadline has passed." | Boundary |
| TC-21 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=0 | 400; INVALID_RATING; "Rating must be an integer between 1 and 5." | Boundary |
| TC-22 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=1 | 201; rating persisted unchanged | Boundary |
| TC-23 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=2 | 201; rating persisted unchanged | Boundary |
| TC-24 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=4 | 201; rating persisted unchanged | Boundary |
| TC-25 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=5 | 201; rating persisted unchanged | Boundary |
| TC-26 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=6 | 400; INVALID_RATING; "Rating must be an integer between 1 and 5." | Boundary |
| TC-27 | US03 | Fresh response; required rating=5; optional text question 2; text_value=whitespace + "a" repeated 1999 times + whitespace; future deadline at frozen T | 201; text of length 1999 persisted | Boundary |
| TC-28 | US03 | Fresh response; required rating=5; optional text question 2; text_value=whitespace + "a" repeated 2000 times + whitespace; future deadline at frozen T | 201; text of length 2000 persisted | Boundary |
| TC-29 | US03 | Fresh response; required rating=5; optional text question 2; text_value=whitespace + "a" repeated 2001 times + whitespace; future deadline at frozen T | 400; TEXT_TOO_LONG; "Text answers cannot exceed 2000 characters." | Boundary |
| TC-30 | US03 | Exactly 5 required rating questions; answer 4 with rating=3; fresh response; deadline=T+2 days at frozen T | 400; MISSING_REQUIRED_ANSWERS; no response persisted | Error |
| TC-31 | US03 | Exactly 5 required rating questions; answer 5 with rating=3; fresh response; deadline=T+2 days at frozen T | 201; exactly one submitted response with 5 answers | Normal |
| TC-32 | US04 | Lecturer 2 assigned to course 1; GET /api/courses/1/feedback; one submitted response, rating=5 and comment="The course content was very useful." | 200; completed_evaluations=1; returned rating and text match | Normal |
| TC-33 | US04 | Lecturer 4 without course assignment; GET /api/courses/1/feedback | 403; FORBIDDEN; "You do not have permission to view this course feedback." | Error |
| TC-34 | US04 | Student session; GET /api/courses/1/feedback | 403; FORBIDDEN | Error |
| TC-35 | US04 | Anonymous GET /api/courses/1/feedback | 401; UNAUTHORIZED | Error |
| TC-36 | US04 | Assigned lecturer; course 1 has one submitted and one draft response | 200; completed_evaluations=1; draft excluded | Normal |
| TC-37 | US04 | Assigned lecturer; 20 distinct enrolled students each have one submitted response in course 1, plus one enrolled draft student; frozen time | 200; completed_evaluations=20; 20 responses; draft excluded; consistent HTML count | Normal |
| TC-38 | US11 | Login with student1@edusurvey.edu / Password123!; POST /api/auth/logout; GET /api/auth/me using the same client | GET returns 401 after logout; logout implementation returns 200, authenticated=false | Normal |
| TC-39 | US11 / US02 | Real student login; verify protected page/API access and seeded evaluation; logout; GET /evaluations and /api/evaluations using the cleared session | HTML 302 to /login; API 401 JSON UNAUTHORIZED; no student data; user_id/role absent | Error |
| TC-40 | US11 / US04 | Real assigned lecturer login; verify seeded submitted feedback is accessible; logout; GET /api/courses/1/feedback | 401 JSON UNAUTHORIZED; no feedback/course data; user_id/role absent | Error |
| TC-41 | US11 | Anonymous POST /api/auth/logout twice; inspect session after each | Both 200 JSON authenticated=false; no redirect; user_id/role absent and auth/me remains 401 | Normal |
| US02-L01 | US02 | Open, unfinished evaluation with deadline=T+12h | 200; Due soon | Normal |
| US02-L02 | US02 | Explicitly closed evaluation with future deadline=T+10 days | 200; Closed | Normal |
| US02-L03 | US02 | Submitted response; evaluation open, deadline=T+10 days | 200; Completed | Normal |
| US02-L04 | US02 | Submitted response; evaluation open, deadline=T-2 days | 200; Completed takes priority over expiry | Normal |
| US02-L05 | US02 | Submitted response; evaluation closed, deadline=T-2 days | 200; Completed takes priority over closed state | Normal |
| US02-L06 | US02 | Student 3 without any enrollment; GET /api/evaluations | 200; exactly {"count":0,"evaluations":[]} | Normal |
| US02-L07 | US02 | Administrator session; GET /api/evaluations | 403; FORBIDDEN; no evaluations key | Error |
| US02-L08 | US02 | Student 1 enrolled only in course 1; student 3 only in course 2, evaluation 4; each supplies the other user/student ID in query | 200; student 1 sees IDs 1,2,3 only; student 3 sees ID 4 only | Normal |
| US02-L09 | US02 | Both students enrolled in course 1; only student 3 submitted evaluation 1 | 200; student 1 sees Active; student 3 sees Completed | Normal |
| US02-L10 | US02 | Student 1 has draft response to open evaluation 1; deadline=T+10 days | 200; Active | Normal |
| US02-L11 | US02 | Evaluation 1 status=draft in enrolled course | 200; only evaluation IDs 2 and 3; unpublished evaluation omitted | Normal |
| TC-US11-01 | US11 | Login with valid credentials | 200; authenticated=true | Normal |
| TC-US11-02 | US11 | Login with incorrect password | 401; INVALID_CREDENTIALS | Error |
| TC-US11-03 | US11 | Anonymous GET /api/auth/me | 401; UNAUTHORIZED | Error |
| TC-US11-04 | US11 | Valid login then GET /api/auth/me | 200; authenticated user information | Normal |
| TC-US11-05 | US11 | Valid login then POST /api/auth/logout | 200; authenticated=false | Normal |
| TC-US11-06 | US11 | Valid login then logout; inspect session | user_id and role are removed | Normal |
| TC-US11-07 | US11 | Valid login then logout; GET /api/auth/me | 401; UNAUTHORIZED | Error |
| TC-US11-08 | US11 | Anonymous POST /api/auth/logout | 200; authenticated=false | Normal |
| TC-US11-09 | US11 | Insert student1@edusurvey.edu again into fixture users table | sqlite3.IntegrityError for duplicate email | Error |
| US01-A01 | US01 | Lecturer demo credentials lecturer1@edusurvey.edu / Password123! | 200; user_id=2, role=lecturer in response and session | Normal |
| US01-A02 | US01 | Administrator demo credentials admin@edusurvey.edu / Password123! | 200; user_id=3, role=administrator in response and session | Normal |
| US01-A03 | US01 | Anonymous GET /api/auth/me | 401; UNAUTHORIZED; no authenticated session | Error |
| US01-A04 | US01 | Anonymous GET /evaluations | HTML 302 to /login; no authenticated session (explicit JSON requests still 401) | Error |
| US01-A05 | US01 | Anonymous GET /evaluations/1/complete | HTML 302 to /login; no authenticated session (explicit JSON requests still 401) | Error |
| US01-A06 | US01 | Anonymous GET /api/evaluations | 401; UNAUTHORIZED; no authenticated session | Error |
| US01-A07 | US01 | Student login then GET /api/auth/me; repeat with independent client | Original client: 200 and exact public student identity; independent client: 401 | Normal |
| US01-A08 | US01 | Student demo login then GET both student pages and list API; no evaluations seeded | Pages: 200 HTML; API: 200 with count=0 and evaluations=[] | Normal |
| US01-A09 | US01 | Lecturer demo login then GET both student pages and list API | All 403; FORBIDDEN | Error |
| US01-A10 | US01 | Administrator demo login then GET both student pages and list API | All 403; FORBIDDEN | Error |
| US01-A11 | US01 | Admin login; insert stale_state into session; login as student | Session contains only user_id=1 and role=student; student page returns 200 | Normal |
| US01-A12 | US01 | Student login; delete that user in temporary database; GET /api/auth/me | 401; message="The authenticated user no longer exists."; session cleared | Error |
| TC-US03-01 | US03 | Fresh enrolled student; required rating=5 and required text="The course is useful." | 201; one response and two answers persisted | Normal |
| TC-US03-02 | US03 | Required rating=5; omit required text question 2 | 400; MISSING_REQUIRED_ANSWERS; zero records created | Error |
| TC-US03-03 | US03 | Existing submitted response with rating=4; resubmit valid payload | 409; DUPLICATE_SUBMISSION; original rating and record counts unchanged | Error |
| TC-US03-04 | US03 | Valid submission; deadline=2000-01-01T00:00:00; frozen now=2026-11-04T12:00:00 | 400; DEADLINE_EXPIRED; zero records | Error |
| TC-US03-05 | US03 | Valid answers; nonexistent evaluation_id=9999 | 404; EVALUATION_NOT_FOUND; zero records | Error |
| TC-US03-06 | US03 | Valid answers; evaluation status=closed | 400; EVALUATION_CLOSED; zero records | Error |
| TC-US03-07 | US03 | Frozen T=2026-11-04T12:00:00; deadline=T-1s | 400; DEADLINE_EXPIRED; zero records | Error |
| TC-US03-08 | US03 | Same frozen T; deadline=T | 400; DEADLINE_EXPIRED; zero records (corrected to main deadline <= now contract) | Error |
| TC-US03-09 | US03 | Same frozen T; deadline=T+1s | 201; one response and two answers persisted | Normal |
| US03-P01 | US03 | Enrolled student; rating=5 and optional text="The course was useful." | 201; persisted response and exact two answers | Normal |
| US04-P01 | US04 | Assigned lecturer GET /lecturer/feedback/1 | 200 HTML with evaluation title, completed count label and submitted comment | Normal |
| US04-P02 | US04 | Anonymous GET /lecturer/feedback/1 | HTML 302 to /login; JSON requests 401 | Error |
| US04-P03 | US04 | Student GET /lecturer/feedback | 403 | Error |
| US04-P04 | US04 | Lecturer GET /lecturer/feedback/999; evaluation nonexistent | 404 | Error |
| TC-US04-01 | US04 | Assigned lecturer GET /lecturer/feedback/1 | 200; evaluation title, completed-count label and seeded comment | Normal |
| TC-US04-02 | US04 | Remove lecturer 2 course assignment; request existing evaluation 1 | 403; "You do not have permission to view this course feedback." | Error |
| TC-US04-03 | US04 | Student GET /lecturer/feedback | 403 | Error |
| TC-US04-04 | US04 | Anonymous GET /lecturer/feedback/1 | HTML 302 to /login; JSON requests 401 | Error |
| TC-US04-05 | US04 | Add draft response/comment DRAFT_ONLY_COMMENT alongside seeded submitted response | 200; draft comment absent, seeded submitted comment present | Normal |
| TC-US04-06 | US04 | Add rating=5 to the seeded submitted response; GET feedback | 200; Student ratings, 5 / 5, Written comments and actual comment displayed | Normal |
| TC-US04-07 | US04 | One seeded submitted response plus one new submitted response and one draft | 200; completed count=2; new submitted comment visible, draft absent | Normal |
| US02-L12 | US02 | Student 1; frozen T=2026-11-03T12:00:00; enrolled evaluations 1/2/3 open with deadlines T+2/3/4 days and no responses; student 3 alone enrolled in a second course with open evaluation 4 | 200; count=3; only IDs 1/2/3; each has exact title, course name, lecturer name, deadline and Active status | Normal |
| TC-US04-08 | US04 | Assigned lecturer; 19 distinct submitted responses and one draft; frozen time | 200; completed_evaluations=19; draft excluded; consistent HTML count | Normal |
| TC-US04-09 | US04 | Assigned lecturer; 21 distinct submitted responses and one draft; frozen time | 200; completed_evaluations=21; draft excluded; consistent HTML count | Normal |

The US02 fixture freezes the route clock before creating data at T=2026-11-03T12:00:00. The Due soon rule is strictly less than 24 hours; tests now check 86399, 86400 and 86401 seconds remaining separately. Deadline equality is Closed; additional tests check T-1s, T and T+1s. Rating boundaries and the five-required-answer submission example below are covered by #184. Five required answers and 20 completed responses are acceptance examples, not implementation maxima.

[The PO-reviewed #188 contract matrix](p0-acceptance-review.md) records the comparison, approved targets, exact future test IDs/nodes, responsible owners, dependencies and diagnostic evidence. Login/duplicate messages must retain the requirements' canonical wording in a future implementation; only the `Due soon` documentation spelling is normalized here after explicit PO approval. Browser logout/protected-HTML navigation must lead to login while APIs retain 200/401 JSON. Browser controls/navigation from #201 are now merged via #218; the approved #214/#215 backend contracts are implemented by this audit, and #202 is merged; copied-cookie revocation remains a separate unresolved decision under #216. The inclusive <=3,000ms budget measures a visible browser outcome including navigation; local Flask timings and whole-suite runtime are not deployed/browser acceptance evidence.

The separate P0C-01–P0C-18 register in that review specifies **future target assertions**, not additional passing current-contract cases in the matrix below. P0C-01/02 reuse existing credential test nodes; P0C-03/04/07 browser cases are now implemented by merged #218 and mapped below; the other proposed redirect/revocation/timing assertions remain pending. All existing case IDs and unrelated pending cases below are retained.

### M5 #201 browser cases (additional to the M4 matrix)

All browser cases below use isolated SQLite data and fixed application time. They exercise the real HTTP/JS interface; the login-message case intercepts one rejected API response to check presentation rather than duplicating API credential partition tests.

| Case ID | Parent / contract | Scenario and expected result |
|---|---|---|
| M5-UI01 | US01 #14, US02 #18, US03 #22 | Public home → login → list → answer/review/submit → reload; server-persisted completion is visible without typing another URL. Phone and laptop layouts have no measured horizontal overflow on login/list/receipt. |
| M5-UI02 / P0C-07 | US11 #183, #188 | Visible keyboard-operated Sign out → `/login`; current session protected API/HTML access returns 401. No copied-cookie revocation or server redirect claim. |
| P0C-03 | US01 #14, #188 | Rejected login displays canonical error plus recovery guidance, button re-enabled. |
| P0C-04 | US02 #18, #188 | T+23h59m59s displays Due soon and is filterable; T+24h displays Active and is excluded by that filter. |
| M5-UI03 | US01 #14, US11 #183 | Lecturer/admin login reaches a valid role page, student API is 403, visible logout works at phone width. |
| M5-UI04 | US03 #22, US11 #183 | Expiry at exactly T after opening rejects submit without writes; failed logout explains recovery and can be retried. |
| M5-UI05 | US02 #18, US03 #22 | Closed/unenrolled evaluation cannot be opened after a stale list; UI explains failure and provides a working list link. |

### M5 #202 lecturer browser cases (US04 #50)

The existing lecturer routes/template now provide useful HTML errors, recovery links, empty states and responsive feedback navigation. APIs retain JSON denials and ownership/submitted-only SQL rules. New cases use the same isolated browser fixture as #201, with frozen domain time.

| Case ID | Scenario | Expected result |
|---|---|---|
| M5-L01 / M5-L02 / P0C-07 | Lecturer logs in, opens assigned feedback, reloads, returns and signs out; phone/laptop + keyboard | Correct counts, ratings/comments; draft/foreign feedback absent; persisted output; logout reaches login and protected requests are 401. Long/HTML-like comments wrap and remain escaped text. |
| M5-L03 | Assigned evaluation with zero responses, then no assignments | Distinct helpful empty states, count 0, working refresh and assignment guidance. |
| M5-L04 | Existing unassigned evaluation / nonexistent evaluation | 403 with exact permission message / 404; no foreign feedback/title; working return-to-list link. |
| M5-L05 | Anonymous, student and administrator open lecturer detail in browser | Anonymous browser redirects to login; wrong-role HTML stays 403 with account recovery; JSON page clients/APIs retain JSON 401/403; no feedback disclosed. |
| M5-L06 | SQLite error while loading lecturer page | Safe 503 explanation with retry; no internal DB detail disclosed; retry succeeds after restoring DB. |

## 3. Automated tests

From the repository root, use Python 3.12 (the CI version; the setup guide currently suggests 3.14):

```bash
python -m venv .venv
source .venv/bin/activate
# Windows activation: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest -v
```

`requirements.txt` pins Flask 3.1.2; `requirements-dev.txt` supplies pytest, coverage, Ruff and Playwright. On Linux use `python -m playwright install --with-deps chromium` for browser system dependencies, as CI does. API tests use the Flask test client; #201 browser fixtures start their own ephemeral loopback server. No manually started Flask process or production database initialization is needed. #201 installed dependencies into a fresh temporary virtual environment; CI provides the separate clean-checkout result.

For a single mapping below, run `python -m pytest -v path/to/test_file.py::test_function`; for example:

```bash
python -m pytest -v tests/test_auth.py::test_login_success
python -m pytest -v tests/test_student_evaluations.py::test_student_evaluations_due_soon_24_hour_boundary
```

All existing mappings below are API integration tests using temporary SQLite databases and Flask's test client. Expected results are specified by the matching Section 2 ID; **PASS** means the existing function passed, not that every source-derived detail in Section 2 is asserted. **NOT IMPLEMENTED** means no corresponding test exists, no function name is proposed as if real, and no pass is claimed.

| Case ID | Pytest function | File | Level / type | Expected / actual verified result | Responsible Sprint 4 task |
|---|---|---|---|---|---|
| TC-01 | `test_login_success[TC-01-student]` | `tests/test_auth.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #165 |
| TC-02 | `test_login_wrong_password` | `tests/test_auth.py` | API integration / error | Section 2 expectation; existing assertions PASS | #165 |
| TC-03 | `test_login_unknown_email` | `tests/test_auth.py` | API integration / error | Section 2 expectation; existing assertions PASS | #165 |
| TC-04 | `test_login_missing_password` | `tests/test_auth.py` | API integration / error | Section 2 expectation; existing assertions PASS | #165 |
| TC-05 | `test_student_evaluations_success` | `tests/test_student_evaluations.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #166 |
| TC-06 | `test_student_evaluations_requires_login` | `tests/test_student_evaluations.py` | API integration / error | Section 2 expectation; existing assertions PASS | #166 |
| TC-07 | `test_student_evaluations_forbidden_for_lecturer[TC-07-lecturer]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-08 | `test_student_evaluations_due_soon_24_hour_boundary[TC-08-below]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-09 | `test_student_evaluations_due_soon_24_hour_boundary[TC-09-at]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-10 | `test_student_evaluations_due_soon_24_hour_boundary[TC-10-above]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-11 | `test_student_evaluations_deadline_boundary[TC-11-before]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-12 | `test_student_evaluations_deadline_boundary[TC-12-at]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-13 | `test_student_evaluations_deadline_boundary[TC-13-after]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-14 | `test_submission_success_persists_response_and_answers` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-15 | `test_submission_missing_required_answers` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #167 |
| TC-16 | `test_duplicate_submission` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #167 |
| TC-17 | `test_submission_requires_login` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #167 |
| TC-18 | `test_submission_deadline_boundary[TC-US03-09-after]` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-19 | `test_submission_deadline_boundary[TC-US03-08-at]` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-20 | `test_submission_deadline_boundary[TC-US03-07-before]` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-21 | `test_submission_rating_boundaries[rating-0]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-22 | `test_submission_rating_boundaries[rating-1]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-23 | `test_submission_rating_boundaries[rating-2]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-24 | `test_submission_rating_boundaries[rating-4]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-25 | `test_submission_rating_boundaries[rating-5]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-26 | `test_submission_rating_boundaries[rating-6]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-27 | `test_submission_text_length_boundaries[length-1999]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-28 | `test_submission_text_length_boundaries[length-2000]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-29 | `test_submission_text_length_boundaries[length-2001]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-30 | `test_submission_required_question_count[answered-4]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-31 | `test_submission_required_question_count[answered-5]` | `tests/test_submission_workflow.py` | API / SQLite integration | Section 2 expectation; PASS in verified #184 run below | #184 / parent US03 #22 |
| TC-32 | `test_lecturer_can_retrieve_course_feedback` | `tests/test_smoke.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #168 |
| TC-33 | `test_lecturer_cannot_access_unassigned_course` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #168 |
| TC-34 | `test_student_cannot_access_lecturer_feedback` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #168 |
| TC-35 | `test_course_feedback_requires_login` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #168 |
| TC-36 | `test_course_feedback_count_excludes_draft_responses` | `tests/test_smoke.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #168 |
| TC-37 | `test_feedback_completed_count[count-20]` | `tests/test_lecturer_feedback.py` | API / HTML / SQLite integration | Section 2 expectation; PASS in verified #185 run below | #185 / parent US04 #50 |
| TC-38 | `test_protected_resource_after_logout_returns_401` | `tests/test_auth.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #169 |
| TC-39 | `test_student_page_denied_after_logout` | `tests/test_auth.py` | Flask client / temporary SQLite | Verified current contract; real results in #186 verification below | #186 / parent #183 |
| TC-40 | `test_lecturer_feedback_denied_after_logout` | `tests/test_auth.py` | Flask client / temporary SQLite | Verified current contract; real results in #186 verification below | #186 / parent #183 |
| TC-41 | `test_anonymous_logout_is_idempotent` | `tests/test_auth.py` | Flask client / temporary SQLite | Verified current contract; real results in #186 verification below | #186 / parent #183 |
| US02-L01 | `test_student_evaluations_due_soon` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L02 | `test_student_evaluations_closed` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L03 | `test_student_evaluations_completed[US02-L03-open]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L04 | `test_student_evaluations_completed[US02-L04-expired]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L05 | `test_student_evaluations_completed[US02-L05-closed]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L06 | `test_student_evaluations_empty` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L07 | `test_student_evaluations_forbidden_for_lecturer[US02-L07-administrator]` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L08 | `test_student_only_sees_evaluations_for_enrolled_courses` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L09 | `test_student_completion_is_personal` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L10 | `test_draft_response_is_not_completed` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| US02-L11 | `test_draft_evaluation_is_hidden` | `tests/test_student_evaluations.py` | API integration | Section 2 expectation; PASS (#166) | #166 |
| TC-US11-01 | `test_login_success[TC-01-student]` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-02 | `test_login_wrong_password` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-03 | `test_current_user_requires_login[US01-A03-me]` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-04 | `test_current_user_after_login` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-05 | `test_logout_success` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-06 | `test_logout_clears_session` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-07 | `test_protected_resource_after_logout_returns_401` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-08 | `test_logout_without_login` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| TC-US11-09 | `test_users_email_unique_constraint` | `tests/test_auth.py` | API / database integration | Section 2 expectation; verified in integration run below | #169 |
| US01-A01 | `test_login_success[US01-A01-lecturer]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A02 | `test_login_success[US01-A02-admin]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A03 | `test_current_user_requires_login[US01-A03-me]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A04 | `test_current_user_requires_login[US01-A04-list-page]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A05 | `test_current_user_requires_login[US01-A05-complete-page]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A06 | `test_current_user_requires_login[US01-A06-list-api]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A07 | `test_current_user_after_login` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A08 | `test_authenticated_student_access[US01-A08-student]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A09 | `test_authenticated_student_access[US01-A09-lecturer]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A10 | `test_authenticated_student_access[US01-A10-admin]` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A11 | `test_login_replaces_previous_session` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| US01-A12 | `test_current_user_deleted_account` | `tests/test_auth.py` | API integration | Expected as Section 2; PASS | #165 |
| TC-US03-01 | `test_submission_success_persists_response_and_answers` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-02 | `test_submission_missing_required_answer_does_not_create_records` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-03 | `test_duplicate_submission_does_not_modify_existing_records` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-04 | `test_submission_after_deadline_does_not_create_records` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-05 | `test_submission_invalid_evaluation_does_not_create_records` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-06 | `test_submission_closed_evaluation_does_not_create_records` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-07 | `test_submission_deadline_boundary[TC-US03-07-before]` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-08 | `test_submission_deadline_boundary[TC-US03-08-at]` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| TC-US03-09 | `test_submission_deadline_boundary[TC-US03-09-after]` | `tests/test_submission_workflow.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| US03-P01 | `test_submit_evaluation_success` | `tests/test_submissions.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #167 |
| US04-P01 | `test_lecturer_can_view_assigned_evaluation_feedback` | `tests/test_lecturer_feedback.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #168 |
| US04-P02 | `test_feedback_page_requires_login` | `tests/test_lecturer_feedback.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #168 |
| US04-P03 | `test_student_cannot_access_lecturer_feedback` | `tests/test_lecturer_feedback.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #168 |
| US04-P04 | `test_lecturer_cannot_view_nonexistent_evaluation` | `tests/test_lecturer_feedback.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #168 |
| TC-US04-01 | `test_lecturer_can_view_assigned_evaluation_feedback` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| TC-US04-02 | `test_lecturer_cannot_view_unassigned_evaluation` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| TC-US04-03 | `test_student_cannot_access_lecturer_feedback` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| TC-US04-04 | `test_feedback_page_requires_login` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| TC-US04-05 | `test_draft_responses_are_excluded_from_feedback` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| TC-US04-06 | `test_feedback_displays_submitted_ratings_and_comments` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| TC-US04-07 | `test_completed_count_includes_only_submitted_responses` | `tests/test_lecturer_feedback.py` | Flask rendering / SQLite integration | Expected as Section 2; verification below | #168 |
| US02-L12 | `test_student_evaluations_three_active` | `tests/test_student_evaluations.py` | API / SQLite integration | Section 2 expectation; PASS in verified #187 run below | #187 |
| TC-US04-08 | `test_feedback_completed_count[count-19]` | `tests/test_lecturer_feedback.py` | API / HTML / SQLite integration | Section 2 expectation; PASS in verified #185 run below | #185 / parent US04 #50 |
| TC-US04-09 | `test_feedback_completed_count[count-21]` | `tests/test_lecturer_feedback.py` | API / HTML / SQLite integration | Section 2 expectation; PASS in verified #185 run below | #185 / parent US04 #50 |

Traceability totals: **97 cases; 97 mapped to existing tests; 0 NOT IMPLEMENTED**. The US02 matrix maps its 21 collected pytest items, including the implemented three-active-evaluation acceptance case. US01 mappings include #181, and the nine original US11 IDs are preserved.

| Story | Documented cases | Existing mappings | Pending |
|---|---:|---:|---:|
| US01 | 16 | 16 | 0 |
| US02 | 21 | 21 | 0 |
| US03 | 28 | 28 | 0 |
| US04 | 19 | 19 | 0 |
| US11 | 13 | 13 | 0 |

**Historical #164 baseline execution, 2026-11-15:** `python -m pytest -v` on macOS, Python 3.12.4, pytest 7.4.4, anyio 4.2.0; exit 0:

```text
collected 63 items
============================== 63 passed in 3.32s ==============================
```

In that historical baseline, all six modules ran: `test_auth.py` (7), `test_feedback_classifier.py` (3), `test_response_schema.py` (3), `test_smoke.py` (35), `test_status.py` (6), and `test_student_evaluations.py` (9). The extra tests cover schema integrity, classification, statistics, evaluation creation/deadline updates and reminders beyond the case matrix. There is no screenshot or verified CI result for this documentation commit.

**Historical #166 actual verification, 2026-11-15:** macOS, Python 3.12.4, pytest 7.4.4, anyio 4.2.0; both commands exited 0:

```text
python -m pytest -v tests/test_student_evaluations.py
20 passed in 0.27s

python -m pytest -v
74 passed in 1.20s
```

No manual server or real database initialization is required. US02 uses no current-date calculation; other modules retain their historical fixture limitations. Its test IDs appear in parameter IDs or function docstrings and every item maps to Section 2/3. The existing #164 mutation evidence below is historical; its line number refers to the original test version, which #166 now parametrizes. No new production bug was found by the #166 test run. CI is not yet verified.

**Integration verification (2026-11-15):** fetched main `ecc0727` baseline: `python -m pytest -v` → **67 passed in 3.02s**. PR #180 after resolution: `python -m pytest -v` → **67 passed in 3.00s**. All legacy US11 scenarios remain linked to actual test functions. Python tests do not establish the unrelated SQL-scanner check passes: CI's `No secrets committed` job rejects tracked `src/feedback_queries.sql` and `src/response_queries.sql` already present on main. No SQL file or scanner rule was changed here.

**Historical #165 verified execution, 2026-11-15:** macOS, Python 3.12.4, pytest 7.4.4, anyio 4.2.0. Both commands exited 0:

```text
python -m pytest -v tests/test_auth.py
17 passed in 2.04s

python -m pytest -v
73 passed in 4.11s
```

The pre-integration authentication module collected 17 items: 16 US01 cases and the retained US11 TC-38 regression. TC-01–TC-04 use their existing identifiers from PR #180; new IDs US01-A01–A12 avoid renumbering the other stories. Each parameter variant has an explicit pytest ID; nonparameterized functions carry the case ID in their docstring. Role-restriction variants each check three resources. No manual Flask server, real database, external service or wall-clock deadline is required. No production defect was found by this run. The #164 historical baseline/mutation evidence below remains distinct from this run; CI verification is pending.

### #186 role-specific logout and idempotency verification

Parent: US11 #183; TC-39 also exercises US02 #18, and TC-40 exercises US04 #50. Three existing pending IDs now map to the exact planned nodes in `tests/test_auth.py`: `test_student_page_denied_after_logout` (TC-39), `test_lecturer_feedback_denied_after_logout` (TC-40), and `test_anonymous_logout_is_idempotent` (TC-41). The current M4 matrix is **97 cases / 83 implemented mappings / 14 pending**; all 13 documented US11 cases have current-contract mappings. Historical totals/runs above remain dated evidence, not current counts.

The new fixture extends only the existing per-test temporary auth SQLite database. It uses `fixed_app_clock` at **2026-11-04T12:00:00**, explicit timestamps for the newly seeded course/enrollment/assignment/evaluation/response rows, an enrolled student, assigned lecturer and real submitted text answer. Tests use real credential login rather than injecting sessions. Before logout, they prove the page/data or lecturer feedback actually succeeds; after logout, they assert the exact 401 JSON error, absent private markers and no Location header. The existing `assert_anonymous` helper checks both `user_id` and `role` are absent and `/api/auth/me` is denied. TC-41 performs two anonymous POSTs, verifying 200/authenticated=false and anonymous session state after each. No application database, manual server or wall-clock deadline is required by these three tests.

Actual local macOS arm64 / Python 3.14.8 / Flask 3.1.2 / pytest 9.2.0 verification on 2026-11-15, based on main `2cb2b05`:

```text
python -m pytest -q tests/test_auth.py
24 passed in 3.05s

PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python -m pytest -q
119 passed in 31.59s
```

The full suite includes the retained Chromium UI cases and all current main regressions; 116 baseline items + 3 new cases, with no skips. PR #219's additional lecturer UI tests remain independent until merged. All pre-existing authentication/TC-US11 test and fixture source was verified byte-for-byte unchanged (the new file starts with the complete main version). Production source is unchanged. Ruff reports the same pre-existing SIM117 finding at `test_users_email_unique_constraint` on both main and this branch; no new finding was introduced. No redirect, copied-cookie revocation (#216), deployed timing or ≤3,000ms acceptance is claimed. Redirect policy remains #215 and requires deliberate future HTML-only expectation updates; this task preserves the current contract.

**PR #181 after integration (2026-11-15):** `python -m pytest -v` → **77 passed in 4.51s**; `python -m pytest -v tests/test_auth.py` → **21 passed in 2.32s**. The suite retains all distinct main US11 tests and all US01 tests; its single `test_logout_clears_session` combines both branches’ assertions. The original `TC-US11-*` IDs remain present. No production source, shared fixture file or SQL scanner was changed.

**PR #182 after integration (2026-11-15):** `python -m pytest -v` → **88 passed in 2.66s**; `python -m pytest -v tests/test_auth.py tests/test_student_evaluations.py` → **41 passed in 2.40s** (21 authentication/US11 and 20 US02 items). Merge dependencies are #180 → #181 → #182. The final matrix has 73 unique IDs, 54 existing mappings and 19 pending cases belonging to US03, US04 and US11. No pending case was marked implemented without a real test. Historical mutation evidence is unchanged.

**US01 CI compatibility correction (2026-11-15):** the credential-pattern scan flagged literal `password=` arguments in the test helper as credential-looking strings, even though they use public demo/invalid test data. Store those explicit values in the named `DEMO_CREDENTIALS` test-data mapping and pass references into the same helper; the default resolves from this mapping. No test assertion, input value, authentication rule or scanner policy changes. The exact CI credential regex now returns no matches locally. After this correction: `python -m pytest -v` → **77 passed in 4.18s**; `python -m pytest -v tests/test_auth.py` → **21 passed in 2.27s**. The separate SQL source-file blocker still requires a repository-policy decision.

**PR #182 final verification after the US01 correction (2026-11-15):** `python -m pytest -v` → **88 passed in 2.61s**; focused authentication and evaluation-list run → **41 passed in 2.39s**. The credential-pattern scan has no matches. This merges the same public-demo test-input correction from #181 without altering any expected authentication result.

**PR #172 integration verification (2026-11-15):** `python -m pytest -v` → **102 passed in 2.73s**; `python -m pytest -v tests/test_submission_workflow.py tests/test_submissions.py` → **10 passed in 0.07s**. The main US01/US02/US11 suites and all original PR tests are retained. The old smoke failure came from an unauthenticated route test opening an uninitialized database; retain main's authenticated/role-aware rendering checks and share the full-schema `api_client` fixture through `conftest.py`.

The integration preserves main's enrollment checks, public response IDs, strict 24-hour threshold, question endpoint, validation/error contract and atomic submission writes; it also retains the PR's lecturer feedback template/routes. The old branch used a three-day Due soon threshold and removed evaluation IDs, which would regress the merged US02 workflow. The original TC-US03-08 expected 201 exactly at deadline; corrected to 400 because main's submission and question routes reject `deadline <= now` and US02 displays Closed at equality. The initial integration run exposed this mismatch (1 failed, 101 passed); production deadline rules were not relaxed to satisfy the old test.

US03/shared API fixtures now freeze application time before use and restore configuration through monkeypatch. The CI SQL-source allowlist is limited to `src/schema.sql`, `src/feedback_queries.sql` and `src/response_queries.sql`; arbitrary SQL dumps, SQLite databases and .env files remain blocked. Existing historical SQL-scanner failures above precede this correction. Performance, copied-cookie replay and still-pending cases are not claimed complete.

**PR #173 integration verification (2026-11-15):** `python -m pytest -v` → **106 passed in 2.83s**; `python -m pytest -v tests/test_lecturer_feedback.py` → **8 passed in 0.06s**. This branch contains the resolved #172 dependency and all current main tests. The lecturer detail route first distinguishes a nonexistent evaluation (404) from an existing evaluation in an unassigned course (403), preserving the required permission message before querying any ratings or comments. All seven original TC-US04 IDs are retained and the eighth test covers nonexistent evaluations. No authentication, enrollment, submission or deadline rule is weakened.

**Issue #188 review verification (2026-11-15, baseline `5a52af6`):** `python -m pytest -v` -> **106 passed in 2.83s** with unchanged test/application source. Reproducible local request diagnostics and all raw samples are documented in [p0-acceptance-review.md](p0-acceptance-review.md) and [p0-local-latency.json](evidence/p0-local-latency.json). Thirty measured samples per operation follow three warm-ups; they exclude browser/network and cannot establish the 3-second user-visible acceptance criterion. The isolated logout probe observed current-client denial (401) but copied-cookie access (200); revocation is NOT established. No browser redirect, target-message regression or deployed timing test is claimed to pass.

**Sprint 4 refinement #163 (2026-11-15):** verified fetched main `5a52af6` with `python -m pytest -v` → **106 passed in 2.95s**. All existing cases and historical evidence are retained; no tests or production code changed for this refinement. Every pending case now names a proposed pytest node and a real open follow-up issue, rather than depending only on closed baseline tasks #167/#168/#169. Proposed nodes are explicitly NOT IMPLEMENTED / NOT RUN. The new US02 three-active example and US04 count-19/count-21 cases are planned; 20 is an acceptance example, not a hard limit. See [sprint4-backlog.md](sprint4-backlog.md) for ownership, hours, dependencies and the verified 21-item Board update (Testing Sprint / Testing Priority / Estimated hours). US11's restored story is #183.

Merge verification for #188 against main `9e5b647` (2026-11-15): `python -m pytest -q` → **106 passed in 3.07s**. The refinement case proposals and historical review diagnostics are both preserved; no new browser/performance result is claimed.

**Issue #187 verification (2026-11-15):** uses the existing per-test `tmp_path` SQLite fixture and application clock frozen at 2026-11-03T12:00:00 before seeding. US02-L12 makes all three enrolled evaluations open with deadlines 48/72/96 hours ahead, seeds another student's course with a valid open evaluation and lecturer assignment, and verifies there are no responses. The Flask-client request must return exactly the three enrolled IDs and all five exact display details with Active status; the other-course record cannot appear. Existing status/boundary tests and production code are unchanged.

Actual local execution on macOS / Python 3.12.4 / pytest 7.4.4 (exit 0):

```text
python -m pytest -v tests/test_student_evaluations.py::test_student_evaluations_three_active
1 passed in 0.04s

python -m pytest -v tests/test_student_evaluations.py
21 passed in 0.15s

python -m pytest -v
107 passed in 2.94s
```

Merge verification against main `9e5b647` (2026-11-15): `python -m pytest -q` → **107 passed in 3.19s**. The merged matrix retains the two planned US04 boundary cases; current totals are 97 cases / 80 implemented mappings / 17 pending.

Only this acceptance example is newly automated. All 17 unrelated pending cases from the merged refinement remain NOT IMPLEMENTED, and historical run/mutation evidence is retained.

Latest #217 integration verification against main `2b644c7` after #213/#218 merged (2026-11-15): `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python -m pytest -q` → **116 passed in 31.46s**. Real browser cases P0C-03/04/07 are now mapped to implemented nodes; API wording, protected-HTML redirects, copied-cookie revocation and deployed timing retain their separate pending scope.

**Fixture and assertion audit / remaining work:**

- #165 completed: authentication fixtures load the real schema into a per-test temporary database; the three demo identities/password match `src/init_db.py`. They do not run the initializer or access the application database. TESTING and SECRET_KEY changes are restored by monkeypatch. TC-01–TC-04 and US01-A01–A12 verify all three roles, credentials, exact credential-error messages, anonymous page/API restrictions, session persistence/isolation/replacement and deleted-account invalidation. Unsupported-role login is not tested because the actual schema rejects unsupported roles; performance and the requirement-message discrepancy remain outside this task.
- #166 completed: the list fixture loads the real schema into a fresh `tmp_path` SQLite database, freezes the application clock before seeding, supplies explicit fixture timestamps, and restores Flask configuration with monkeypatch. Twenty individually traceable items cover retrieval, anonymous/role denial, disjoint enrollment and query impersonation attempts, personal completion status, empty lists, all four display statuses, draft states, completion precedence, and both exact time boundaries. Authentication is injected through `session_transaction()` to isolate US02; credential login remains US01. The retrieval case checks three total evaluations including closed, not three active evaluations.
- #167 integrated: successful persistence, rejection without writes, duplicate immutability and exact deadline boundaries now have real workflow tests and frozen time. Rating/text numerical boundaries and the five-required-question acceptance example are covered by #184; new/draft submission rollback after an injected second-answer failure is covered by #189 (see audit below). Existing smoke rejection tests remain intact.
- #168 integrated: retain all eight lecturer-page tests, including ownership denial for an existing evaluation (403), nonexistent evaluation (404), anonymous/student restrictions, draft exclusion, submitted ratings/comments and completed counts. Existing course-feedback API tests remain intact. The 19/20/21-response acceptance examples are covered by #185; broader statistics/topic access control remains outside these tests.
- #169 integrated: retain logout success, session clearing, post-logout `/api/auth/me` denial, anonymous logout and duplicate-email coverage and all nine legacy IDs. TC-39/40/41 (#186) now verify role-specific current-session denial and repeated anonymous logout. Server HTML redirects and saved-cookie replay remain separate pending contracts; browser logout navigation has #201 evidence. Flask uses a signed client-side cookie and logout calls `session.clear()`; server-side revocation of a copied old cookie is not demonstrated. Shared app configuration is changed by fixtures without comprehensive restoration; centralize isolated fixtures and freeze both Python time and SQL timestamps where assertions depend on time.

Schema tests explicitly enable foreign keys on `:memory:` SQLite. Smoke tests load the real schema into `tmp_path`; other fixtures create reduced schemas, so they cannot establish all production constraints. Some smoke fixture rows use SQLite `CURRENT_TIMESTAMP`, which Python clock patching does not control. Current tests avoid the real application database, but the suite does **not yet satisfy** the stricter requirement to avoid uncontrolled current dates everywhere. Issue #166 changes only this documentation and `tests/test_student_evaluations.py`; no production logic is changed. Authentication fixtures now include PR #181 and the main US11 assertions; all distinct tests are preserved.

### #201 browser mapping and actual result

All nodes below are in `tests/test_p0_browser_contracts.py`:

| Case ID | Actual pytest node suffix |
|---|---|
| M5-UI01, M5-UI02, P0C-07 | `test_logout_navigates_to_login[laptop]`, `test_logout_navigates_to_login[phone]` |
| P0C-03 | `test_login_error_visible_message` |
| P0C-04 | `test_due_soon_label_and_filter` |
| M5-UI03 | `test_role_landing_and_logout[lecturer@test.com-/lecturer/feedback]`, `test_role_landing_and_logout[admin@test.com-/account]` |
| M5-UI04 | `test_submission_deadline_race_and_retryable_logout` |
| M5-UI05 | `test_open_evaluation_error_explains_next_action[closed]`, `test_open_evaluation_error_explains_next_action[unenrolled]` |

Local 2026-11-15: `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python -m pytest -q --cov --cov-report=term --junitxml=/private/tmp/201-junit.xml` → **115 passed, 214 warnings in 29.67s**, no skips. Existing 106 tests are preserved. SQLite ResourceWarnings on Python 3.14 and pre-existing app lint findings are not resolved by this frontend task. The successful run preceded a node-only rename of the combined walkthrough to the approved P0C-07 proposal `test_logout_navigates_to_login`; assertions are unchanged. CI verifies the final node names separately. See [setup, environment, screenshots and limits](p0-student-navigation.md). Pytest elapsed time is not acceptance timing evidence; public browser timing, redirects #215 and replay revocation #216 retain their pending status.

### #202 mapping and verified execution

All nodes are in `tests/test_p0_browser_contracts.py`; existing mappings above are unchanged.

| Case IDs | Actual node suffixes |
|---|---|
| M5-L01, M5-L02, P0C-07 | `test_lecturer_feedback_click_through[laptop]`, `[phone]` |
| M5-L03 | `test_lecturer_feedback_empty_states` |
| M5-L04 | `test_lecturer_feedback_access_error_recovery[/lecturer/feedback/2-403]`, `[/lecturer/feedback/999-404]` |
| M5-L05 | `test_lecturer_feedback_wrong_role_browser_errors[anonymous]`, `[student]`, `[administrator]` |
| M5-L06 | `test_lecturer_feedback_unavailable_retry` |

2026-11-15 local command: `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' P0_SCREENSHOT_DIR=/private/tmp/p0-202-screenshots python -m pytest -q` → **125 passed in 49.21s**, no skips (116 retained + 9 new variants). After a final empty-answer guidance clarification, `python -m pytest -q tests/test_lecturer_feedback.py` → **8 passed in 0.08s**. [Lecturer evidence](p0-lecturer-feedback.md) records environment, seeded-account walkthroughs, screenshots and limits. Public deployment/physical phone/timing remain pending; pytest duration is not a performance measurement. #202 introduces browser HTML error presentation at unchanged denial statuses, not #215's future redirects or #216's cookie revocation.

### Backend audit: approved P0 contracts and M5 runtime

Latest integration (2026-11-15): merged main `dff0de8` after #220/#222 landed. Full local regression: **183 passed in 56.15s** with `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python -m pytest -q`. Earlier 169-test results describe the pre-merge baseline. All new main tests are retained; no skipped test is introduced.

P0C-01/02 reuse `tests/test_auth.py::test_login_wrong_password` and `::test_login_unknown_email` for canonical messages; no duplicate credential scenarios are added. P0C-05/06 are implemented in `tests/test_submission_workflow.py::test_duplicate_submission_canonical_message` and `::test_duplicate_questions_canonical_message`, including preserved stored answers/counts. P0C-08 is `tests/test_auth.py::test_protected_html_redirects_after_logout` with student, lecturer and administrator variants; all protected HTML follow-ups reach login while API denials remain JSON 401.

Runtime/security tests are in `tests/test_backend_runtime.py`, using isolated SQLite/fixed domain clocks where applicable:

| IDs | Node names | Verified behavior |
|---|---|---|
| BE-01 | `test_health_database_check[ready/missing/empty/corrupt]` | Real DB readiness 200/503; no replacement file created. |
| BE-02 | `test_request_logs_exclude_user_input` | Endpoint/status/duration events omit raw URL/query/body/cookie/input markers. |
| BE-03 | `test_feedback_aggregate_permissions` (15 endpoint/identity variants) | Three aggregate APIs: anonymous 401, student/admin/unassigned lecturer 403, assigned lecturer 200; no leaked feedback. |
| BE-04 | `test_missing_database_is_safe_503` | DB unavailable yields actionable safe response, no private detail or new empty file. |
| BE-05 | `test_production_config_requires_explicit_secrets_and_storage` (5 variants) | Production secret/path guards and secure cookie config. |
| BE-06 | `test_database_transaction_closes_and_rolls_back` | Runtime FK enforcement, rollback and connection closure. |
| BE-07/08 | `test_online_backup_and_restore_round_trip`, `test_backup_missing_source_creates_no_output` | Consistent backup/restored copy, private file permissions, no overwrite/empty-file fallback. |
| BE-09 | `test_production_initializer_refuses_reset` | Existing production DB cannot be reset by initializer. |
| BE-10 | `test_unexpected_errors_are_sanitized` | Safe 500 with observable exception type, no private exception input. |
| BE-11 | `test_fresh_m5_demo_has_student_work_and_lecturer_feedback` | New opt-in demo has fresh student slot, existing submitted feedback, future deadlines and valid FKs; second initialization refused. |
| BE-12 | `test_offset_deadlines_consistent_across_p0` (4 variants) | +07:00 ISO dates at T+86399/86400/86401 seconds and T; list/questions/submission agree, strict 24h and expiry equality retained. |

Actual local verification (2026-11-15, macOS arm64 / Python 3.14.8 / Flask 3.1.2 / Playwright 1.65.2 / Chrome 157.0.8103.78): `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python -m pytest -q` → **169 passed in 54.47s**, no skips (128 retained scenarios + 41 additional variants). The duplicate tests then strengthened preserved-answer/count assertions without changing code; focused rerun → **2 passed in 0.12s**. New runtime module/test/backup/Gunicorn config Ruff checks pass; existing unrelated lint findings remain. CI verifies the final tree on Linux/Python 3.12. These durations are test execution time, not user-visible latency evidence.

The M4 97-case matrix and M5 UI tables remain separate from this additional runtime register. Existing test scenarios are preserved; some intentionally change expectations under #214/#215 or authenticate aggregate tests under the new ownership requirement. No skips, production-data tests, copied-cookie revocation or deployed timing pass is introduced. Gunicorn local production-mode smoke used only temporary data and passed readiness 200→missing DB 503→restored DB 200, secure cookie headers, HTML redirect and sanitized telemetry. Hosting, persistent-volume configuration, actual log dashboard/alarms, deployment-gating/rollback and public HTTPS checks remain unverified.

## 4. What the tests found

#201 source review found lecturer/admin login destinations with no routes and submission UI text claiming saving was unavailable after the backend already persisted responses. The branch fixes those integration gaps, adds session controls and verifies the corrected workflow in Chromium. An initial browser attempt targeted the visually overlaid radio input and timed out; the test was corrected to use the visible label and then keyboard activation. Another new test selected two identically named Back links; scoping it to the error panel fixed the test selector. Neither test-authoring issue was hidden by a skip. Existing baseline and mutation evidence below remains historical.

No previously unknown production defect was established by the baseline run: all 63 tests passed. The requirement discrepancies and coverage risks above are source-review findings, not fabricated failing-test results. To demonstrate actual defect detection, a controlled mutation was executed against a disposable copy of `src/` and `tests/` created with Python `tempfile.TemporaryDirectory`; the repository's application code and real database were untouched.

| Evidence | Observed detail |
|---|---|
| Business rule | An unfinished open evaluation is Due soon only when time remaining is strictly below 24 hours; exactly 24 hours is Active. |
| Injected defect | In copied `src/app.py`, replace `and deadline < now + timedelta(hours=24)` with `and deadline <= now + timedelta(hours=24)`. |
| Root cause | Making the comparison inclusive incorrectly includes the upper boundary in Due soon. |
| Detecting regression test | `tests/test_student_evaluations.py::test_student_evaluations_due_soon_24_hour_boundary`, covering TC-08 and TC-09. |
| Command in temporary copy | `python -m pytest -v tests/test_student_evaluations.py::test_student_evaluations_due_soon_24_hour_boundary` |
| Original failing behavior under mutation | At fixed 2026-11-03T12:00:00 with a deadline exactly 24 hours later, the API returned Due soon instead of Active. |
| Actual failing result | Exit 1; `1 failed in 0.31s`; assertion at `tests/test_student_evaluations.py:369`: `assert 'Due soon' == 'Active'`. |
| Corrective action | Restore the copied source text to the original strict comparison before rerunning the same test. |
| Actual restored result | Exit 0; `1 passed in 0.25s`. |
| Cleanup | Temporary copy removed automatically. Original `src/app.py` remained unchanged throughout. No intentionally broken code is included. |

This proves the existing boundary test detects this specific mutation; it is not a claim of a production bug fix or comprehensive mutation coverage. Completion still requires the pending tests assigned to #165–#169, resolution of the requirements/implementation discrepancies, controlled-time fixture improvements, browser/performance evidence where required, and independent teammate review. Passing baseline tests alone does not close these acceptance gaps.

## US03 boundary verification - #184 (2026-11-15)

TC-21 through TC-31 trace to parent US03 #22 through #184. They extend the existing
#167 persistence/deadline baseline without duplicating those tests. Each parameter
uses a fresh temporary SQLite database, an enrolled student, an open evaluation,
frozen T=2026-11-03T12:00:00 and deadline T+2 days. Text cases use an optional
text question with surrounding whitespace; assertions verify the exact trimmed
text at 1999/2000 characters. Rejected rating/text/missing-answer cases preserve
both response and answer counts. The five-question cases seed exactly five
required ratings; the successful case verifies one submitted response and all
five exact answers. Five is an acceptance example, not a maximum.

Actual local execution: Windows, Python 3.12.6, pytest 9.0.2:

```text
python -m pytest -v tests/test_submission_workflow.py
20 passed in 2.66s

python -m ruff check tests/test_submission_workflow.py
All checks passed!

# PowerShell; installed Google Chrome used for the existing browser tests
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
python -m pytest -q --cov --cov-report=term --junitxml=junit.xml
127 passed in 79.87s (0:01:19)
```

The workflow run includes all 11 new parameter variants and all 9 existing
workflow cases, including rejection at deadline equality. The initial sandboxed
attempt could not access pytest's temporary directory and produced 20 setup
errors; the successful run above used normal access to the temporary directory.
No failing tests were skipped and production code was unchanged.
The full run had zero failures/errors/skips and preserved the existing US02
24-hour boundaries and US03 deadline-equality behavior. Coverage reported 95%
overall (including tests) and 89% for `src/app.py`; this is local execution,
not a claimed CI result or deployed performance measurement.

### #184 merge verification against main 33cc07d

Preserved the #202 lecturer UI evidence and #186 logout mappings while retaining
all 11 US03 boundary variants. Traceability totals include #184 and #186; the
separate #185 PR is not included. Windows/Python 3.12.6, same Chrome executable
setting above: `python -m pytest -q --junitxml=junit.xml` ->
**139 passed in 131.68s**, no skips. Changed-module Ruff and `git diff --check`
passed. No production code or submission/deadline assertions were changed by
this conflict resolution.

## US04 completed-count verification - #185 (2026-11-15)

TC-US04-08/count-19, TC-37/count-20 and TC-US04-09/count-21 trace to parent
US04 #50 through #185. Twenty is an acceptance example, not a maximum or an
access boundary: all three cases return 200 and exactly N completed evaluations.
The existing access-denial tests are retained without duplication.

Each parameter uses the Flask client and a fresh temporary SQLite database from
`api_client`, with the route clock frozen at T=2026-11-04T12:00:00 by
`fixed_app_clock`. The fixture's original response is removed before seeding N
distinct enrolled submitted students and one additional enrolled draft student.
Lecturer 2 remains assigned to course 1. Seed timestamps are explicit: creation,
enrollment and assignment at T-1 day, submissions at T-2 hours, deadline T+2 days;
the draft has NULL submitted_at. Foreign keys are enabled while seeding.

Every response has a rating and text answer. Assertions verify the API count,
exactly N returned feedback entries, draft comment exclusion from both API and
HTML, and the number attached to the HTML Completed evaluations label. Thus the
count is checked against responses rather than answer rows.

Actual local execution: Windows / Python 3.12.6 / pytest 9.0.2:

```text
python -m pytest -v tests/test_lecturer_feedback.py
11 passed in 1.44s

python -m ruff check tests/test_lecturer_feedback.py
All checks passed!

# PowerShell; installed Google Chrome used for existing browser tests
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
python -m pytest -q --cov --cov-report=term --junitxml=junit.xml
119 passed in 75.81s (0:01:15)
```

The focused run includes three new parameter variants and all eight existing
lecturer tests. Production code is unchanged. Results here are local execution,
not a claimed CI result or deployed performance measurement.
The full run on main `2cb2b05` plus this task had zero failures/errors/skips,
including the existing access-denial, browser, 24-hour and deadline-equality
tests. Coverage was 95% overall (including tests) and 88% for `src/app.py`.
The separate #184 submission-boundary PR is not included in this branch.

### #185 merge verification against main 33cc07d

Merged the #202 lecturer UI and #186 logout evidence without dropping their
mappings. Totals now include both #185 and #186. Updated the label-bound count
assertion for the new `data-completed-count` wrapper; production code is unchanged
by this conflict resolution. The first integration run used the old assertion
and reported 3 failed / 128 passed; all three failures were the wrapper mismatch.
After correction: `python -m pytest -q tests/test_lecturer_feedback.py` ->
**11 passed in 2.68s**; changed-module Ruff and `git diff --check` passed.
Full Windows/Python 3.12.6 run with the same Chrome executable setting above:
`python -m pytest -q --junitxml=junit.xml` -> **131 passed in 114.71s**, no skips.

### #185 verification after #220 merged into main f7b073b

Combined the merged #184 US03 mappings/results with #185 US04 mappings/results
without discarding either evidence section. The matrix now has 97 documented
cases, 97 existing mappings and zero NOT IMPLEMENTED mappings; this does not
claim that broader release/review/performance evidence is complete.
Windows/Python 3.12.6, same Chrome executable setting above:
`python -m pytest -q --junitxml=junit.xml` -> **142 passed in 113.99s**, no skips.
`python -m ruff check tests/test_lecturer_feedback.py tests/test_submission_workflow.py`
and `git diff --check` passed. This merge resolution changes documentation only;
both task implementations and all existing tests are retained.

## Database fixture and transaction audit - #189 (2026-11-15)

Historical pre-#223 evidence follows. Runtime FK/error-handling findings are
superseded by the #205 and #206 integration verification below; original results are retained.

Parent US11 #183 / refinement #163 owns this audit. Cross-story dependencies are
US03 #22 for response/answer integrity and submission atomicity, and US04 #50
for submitted-only feedback queries. These audit IDs are separate from the
97 story-case matrix above; reused schema tests are not duplicated.

| Audit ID | Real pytest node | Dependency / verified decision |
|---|---|---|
| DB-189-01 | `tests/test_database_integrity.py::test_schema_rejects_orphans[evaluation]` | US03 #22: missing response evaluation rejected with FK ON |
| DB-189-02 | `tests/test_database_integrity.py::test_schema_rejects_orphans[student]` | US03 #22: missing response student rejected with FK ON |
| DB-189-03 | `tests/test_database_integrity.py::test_schema_rejects_orphans[response]` | US03 #22: missing answer response rejected with FK ON |
| DB-189-04 | `tests/test_database_integrity.py::test_schema_rejects_orphans[question]` | US03 #22: missing answer question rejected with FK ON |
| DB-189-05 | `tests/test_response_schema.py::ResponseSchemaTests::test_student_cannot_have_duplicate_response` | Reused: UNIQUE(evaluation_id, student_id) |
| DB-189-06 | `tests/test_response_schema.py::ResponseSchemaTests::test_question_cannot_have_duplicate_answer_in_response` | Reused: UNIQUE(response_id, question_id) |
| DB-189-07 | `tests/test_database_integrity.py::test_submission_write_failure_rolls_back[new]` | US03 #22: no partial response/answer after write failure; retry succeeds |
| DB-189-08 | `tests/test_database_integrity.py::test_submission_write_failure_rolls_back[draft]` | US03 #22: exact draft response/answers restored after deletion and partial replacement; retry succeeds |
| DB-189-F01 | `tests/test_database_integrity.py::test_runtime_foreign_keys_finding` | Diagnostic finding: production factory returns FK OFF; orphan accepted, then explicitly rolled back |
| DB-189-09 | `tests/test_response_schema.py::ResponseSchemaTests::test_submission_status_and_timestamp_are_stored` | Reused explicit timestamp/status persistence assertion |

All ten mappings passed in the focused run below (seven new variants plus three
retained schema tests). The four rejection tests use a fresh temporary connection,
assert FK=1 before writes, check the seed for violations and preserve both table
counts. The runtime diagnostic uses two fresh connections from the unmodified
production factory, both pointing at the monkeypatched temporary database. It
asserts FK=0, demonstrates an orphan and `foreign_key_check` violation, rolls it
back, and verifies a clean database from a second connection. A passing diagnostic
records the defect; it does not mean production FK enforcement is working. If
production is fixed separately, this characterization test must be updated.

Rollback tests use Flask `POST /api/submissions` with the real connection factory
and transaction context. A test-only SQLite BEFORE INSERT trigger raises ABORT
on question 2 only after question 1 with rating 5 exists in the same transaction.
ABORT cancels only the failing statement, so exact snapshots from a fresh
connection establish rollback of prior response creation, draft answer deletion
and the first answer write. Removing only the trigger permits a successful retry
with exact persisted answers. TESTING propagates IntegrityError: safe production
500/error recovery presentation is not established by these tests. Commit-time
I/O failures and concurrent writes remain outside this injection coverage.

### Fixture and query review

- `tests/conftest.py`: each fixture uses tmp_path, monkeypatch restores DATABASE,
  TESTING, SECRET_KEY and TEST_DATABASE (including removal if originally absent).
  Seed connections now close explicitly using `closing`; both test clients use
  context managers. No initializer or real data database is opened by new tests.
- The shared API fixture uses frozen T=2026-11-04T12:00:00 for submitted_at and
  normalizes created/enrollment/assignment timestamps explicitly. Python's clock
  does not control SQLite: rollback tests register a test-only current_timestamp
  function on runtime connections to make exact retry timestamp assertions stable.
- `tests/test_response_schema.py`: retained all three existing tests; added an
  explicit FK=1 assertion on their in-memory connection. Schema loading's PRAGMA
  applies only to that connection, not connections opened later by the app.
- `src/schema.sql`: foreign keys cover both response parents and both answer
  parents; both requested UNIQUE constraints already exist. It does not enforce
  question.evaluation_id == response.evaluation_id through a composite FK.
- `src/response_queries.sql`: reference statements use bound named parameters,
  uniqueness-based draft/upsert handling, and CURRENT_TIMESTAMP for submission.
  They do not wrap the multi-statement workflow in a transaction themselves;
  callers must supply ownership, type, deadline checks and a transaction. The
  current Flask submission route uses inline SQL in a connection context instead.
- `src/feedback_queries.sql` and `src/feedback_queries.py`: submitted-only filters
  and same-evaluation question joins are present; ownership is a caller
  responsibility. Static review here does not claim every reference SQL statement
  was independently executed. Existing API/lecturer tests retain runtime coverage.

### Findings and unresolved work

**DB-189-F01:** `src/app.py::get_db_connection` does not enable per-connection FK
checks. Orphan acceptance was reproduced only on a temporary database. No
production/schema setting is changed in this PR. A separately reviewed production
fix must reference #189 / DB-189-F01 and re-run the integration suite, including
existing fixtures that intentionally contain inconsistent data.

**DB-189-F02:** legacy reduced-schema login fixtures, SQL CURRENT_TIMESTAMP in
smoke helpers and other fixture defaults, and some SQLite connections relying on
implicit cleanup remain. This PR improves shared fixture cleanup/time control;
it does not claim a repository-wide deterministic SQL clock or closed-connection
audit. Python datetime freezing alone never establishes SQLite timestamp control.

The initial focused run had 2 failed / 8 passed because retry timestamp assertions
assumed SQL time followed the frozen Python clock. Test-only SQL clock control
corrected that assumption; production timestamp behavior was not changed.

Actual Windows / Python 3.12.6 / pytest 9.0.2 execution:

```text
python -m pytest -v tests/test_database_integrity.py tests/test_response_schema.py
10 passed in 0.88s

python -m ruff check tests/conftest.py tests/test_database_integrity.py tests/test_response_schema.py
All checks passed!
```

No failing tests are skipped. Broader production remediation and independent
teammate review remain pending; local execution is not deployed performance evidence.

Full-suite verification on main `dff0de8` plus #189 (Windows/Python 3.12.6):

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
python -m pytest -q --junitxml=junit.xml
# 149 passed in 122.47s (0:02:02)
```

JUnit confirms 149 tests, zero errors/failures/skips (142 retained + 7 new audit
variants). Existing browser, authentication/logout, feedback, uniqueness and
submission/deadline cases are retained. No schema, production route or SQL helper
was changed. CI verification is separate from this local result.

## #204 production database, demo persistence and isolated recovery

Parent #200; interfaces with deployment #205 and operations #208. The schema
and production routes are retained. New initialization publishes only a fully
seeded private file without replacing an existing target. Backup validation
now rejects FK-invalid source/copy data; `tools.verify_database` validates
read-only and compares the complete offline schema/data/sequence dump.

All nodes below are in `tests/test_production_database.py`; dependencies include
US01 #14 (real role login), US02 #18 (usable evaluations), US03 #22 (committed
submission) and US04 #50 (restored submitted feedback).

| Evidence / dependency | Real pytest node suffix | Verified result |
|---|---|---|
| DB204-01 / #14,#18,#50 | `test_demo_roles_have_usable_landing[student1@edusurvey.edu-student-/evaluations]`, `[lecturer1@edusurvey.edu-lecturer-/lecturer/feedback]`, `[admin@edusurvey.edu-administrator-/account]` | Three canonical demo credentials work; student active work, lecturer feedback and administrator landing exist |
| DB204-02 / #204,#205 | `test_initializer_preserves_existing_file[production]`, `[development]` | Both environments refuse repeat initialization; existing bytes preserved |
| DB204-03 / #204 | `test_failed_initialization_leaves_no_published_database` | Injected seed failure publishes no partial file and cleans temporary output |
| DB204-04 / #204,#205 | `test_initializer_never_overwrites_concurrent_winner` | Late concurrent target is preserved; exclusive publication fails closed |
| DB204-05 / #204,#205 | `test_platform_environment_and_new_process_read` | Separate process imports production env path/secure cookies and reads health |
| DB204-06 / #22,#50,#204 | `test_actual_backup_restore_preserves_snapshot` | Real API submission backed up/restored; full schema/rows/sequences equal; later source edit excluded; restored role workflows and no-overwrite checks pass |
| DB204-07 / #22,#204 | `test_created_record_survives_new_process` | A committed submission/answers survive a separate application process |
| DB204-08 / #204 | `test_backup_rejects_invalid_source_without_output[missing]`, `[corrupt]`, `[foreign-key]` | Reject invalid source; no output or source mutation |
| DB204-09 / #204 | `test_failed_backup_removes_only_its_partial_output` | Injected online-copy failure removes partial copy and preserves source |
| DB204-10 / #204 | `test_readonly_verification_never_creates_missing_file` | Missing verification path fails without creating a file |
| DB204-11 / #18,#22,#204 | `test_seeded_submission_survives_browser_reload` | Chromium uses full M5 seed; real login, two ratings/comment, submit, reload; completion and exactly one response/three answers persist |

The fixture freezes application time, initializes only under tmp_path and
restores environment/configuration via monkeypatch. Browser HTTP runs on a
fixture-owned ephemeral loopback server; only that local fixture disables
Secure cookies. Production HTTPS behavior is unchanged. Seed SQL default
timestamps are not claimed to follow Python's frozen time; assertions compare
actual snapshots rather than invented timestamp values.

Main advanced to `6acf0dd` while this task was being prepared. The baseline
test-contract fixes from merged deployment PR #226 are retained exactly;
this PR does not introduce a competing baseline implementation. DB-189-F01
checks orphan rejection on two FK-enabled runtime connections; rollback variants
assert sanitized 503, exact draft/new snapshots and a successful retry. BE-05
uses native absolute paths; BE-07 verifies requested creation mode 0600 and
POSIX effective permissions, preserving restore/no-overwrite checks. Windows
ACLs remain an operator requirement. No tests are skipped or removed.

Actual execution by OpenAI Codex (AI-assisted, not a separate teammate run),
Windows NT 10.0.26200.0 / Python 3.11.9 / pytest 9.2.0 / Flask 3.1.2 /
Playwright 1.65.2 / installed Chrome 157.0.8103.51:

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .venv/m4-env/Scripts/python.exe -m pytest -v --cov --cov-report=term-missing --junitxml=docs/evidence/204/pytest.xml
# 206 passed in 56.91s; exit 0; no errors/failures/skips
```

[Console](evidence/204/pytest.txt) and [JUnit](evidence/204/pytest.xml) retain
the actual run. The initial 15-case focused run passed before adding the
separate-process committed-record case and strengthening restored-role checks;
the full run above includes all 16 final cases. Ruff on all changed Python
files and `git diff --check` passed. This is not measured production latency.

An additional CLI drill used a TemporaryDirectory: `python -m src.init_db
--m5-demo`, insert a synthetic recovery marker, `python tools/backup_database.py
source.db snapshot.db`, edit the original marker, copy snapshot to restored,
then `python -m tools.verify_database snapshot.db --compare restored.db`.
Integrity/FK/schema/data comparison passed; restored marker retained its
pre-backup value. [Actual commands/results](evidence/204/restore-check.json)
contain only statuses/counts and synthetic temporary paths. The corrected
drill explicitly closes SQLite handles before removing all its temporary files.

Pending external evidence: actual paid mount/URL, restart and redeploy survival,
off-host backup transfer/scheduling and host-level restore under #205/#208,
plus a teammate's independent review. Local tests do not certify those actions.

### #204 integration verification with merged #205

Integrated main **6acf0dd** (PR #226); resolved the documentation-only conflict
by preserving both #204 and #205 evidence sections. Baseline runtime tests are
byte-identical to main. No deployment workflow, Blueprint or startup guard
was replaced. The shared initializer remains compatible with the guard's
explicit opt-in, provisioned marker and repeat-startup preservation checks.

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .venv/m4-env/Scripts/python.exe -m pytest -v --cov --cov-report=term-missing --junitxml=docs/evidence/204/integrated-pytest.xml
# 216 passed in 58.86s; exit 0; zero failures/errors/skips
```

Same Windows/Python 3.11.9 environment: 200 retained main cases + 16 new #204
cases. [Integrated console](evidence/204/integrated-pytest.txt) and
[JUnit](evidence/204/integrated-pytest.xml) are separate from the earlier
206-case pre-merge run. Changed-module Ruff and `git diff --check` passed.

## Deployment preparation and main integration - #205 (2026-11-15)

Parent #200; dependencies #204/#207. Real deployment/public HTTPS, paid-account
approval, failing-CI/provider rehearsal and hosted rollback remain pending.
See [deployment handover](deployment.md) for exact settings, runbook and limits.

The first full Windows run on main 686bd9e plus deployment preparation reported
**5 failed / 195 passed in 135.87s**. It exposed three stale #189 assertions after
#223 enabled runtime FK and sanitized SQLite errors, and two POSIX-specific
assumptions in #223 tests. No production contract was weakened to pass tests.

DB-189-F01 retains `test_runtime_foreign_keys_finding` but now asserts FK=1 on
two fresh runtime connections and actual orphan rejection: #223 resolves the old
FK-OFF finding. DB-189-07/08 retain the real second-answer trigger, exact rollback
snapshots and successful retry; they now assert sanitized 503 DATABASE_UNAVAILABLE
instead of an exception escaping Flask. SQL time remains explicitly controlled.

BE-05 uses tmp_path for a genuinely absolute path on either operating system.
BE-07 verifies the backup requests mode 0600 on all systems, and additionally
checks effective POSIX permission bits on POSIX. Windows ACL privacy is not
established by Unix mode bits; the actual backup/restore/overwrite checks run on
both platforms. No test is skipped. Existing audit-run evidence remains historical.

| ID | Real pytest node | Scope |
|---|---|---|
| DEP-205-01 | `tests/test_deployment.py::test_production_restart_preserves_data` | New opt-in bootstrap, byte-identical restart, missing-after-provision refusal |
| DEP-205-02 | `tests/test_deployment.py::test_bootstrap_fails_closed[no-opt-in]` | Missing DB cannot seed without opt-in |
| DEP-205-03 | `tests/test_deployment.py::test_bootstrap_fails_closed[no-mount]` | Absent persistent mount cannot seed |
| DEP-205-04 | `tests/test_deployment.py::test_bootstrap_fails_closed[corrupt]` | Corrupt existing DB is never reset |
| DEP-205-05 | `tests/test_deployment.py::test_deploy_rejects_pr_before_provider_call` | PR context rejected before API call |
| DEP-205-06 | `tests/test_deployment.py::test_deploy_exact_sha_and_readiness[auto-deploy]` | Reject competing platform auto-deploy before POST |
| DEP-205-07 | `tests/test_deployment.py::test_deploy_exact_sha_and_readiness[wrong-repo]` | Reject wrong service repository before POST |
| DEP-205-08 | `tests/test_deployment.py::test_deploy_exact_sha_and_readiness[wrong-sha]` | Reject provider's live SHA mismatch |
| DEP-205-09 | `tests/test_deployment.py::test_deploy_exact_sha_and_readiness[failed-build]` | Failed build cannot be reported ready |
| DEP-205-10 | `tests/test_deployment.py::test_deploy_exact_sha_and_readiness[ready]` | Exact-SHA POST and HTTPS health contract through fake provider |

These ten tests use temporary data/fake API; they do not prove real deployment
or a failed GitHub test preventing a provider release. Startup dates are only
used to seed relative demo availability, not asserted against wall time. Tests
restore environment, mount mock and initializer globals. Config/factory guards
already verified in #223 are reused rather than duplicated.

Executed on Windows/Python 3.12.6:
`python -m pytest -q tests/test_deployment.py tests/test_database_integrity.py tests/test_backend_runtime.py`
-> **53 passed in 5.01s**. Changed Python modules passed Ruff, YAML dependency/
security-step/mount checks passed, and `git diff --check` passed.

Final full local verification (Windows/Python 3.12.6, installed Chrome selected via
PLAYWRIGHT_CHROMIUM_EXECUTABLE): `python -m pytest -q --junitxml=junit.xml` ->
**200 passed in 118.32s (0:01:58)**, zero failures/errors/skips. This includes the
existing 190 collected cases on main 686bd9e and ten new deployment cases.
Real hosting, paid-resource approval, CI red-test gate proof, rollback and release
verification remain pending; a local green suite does not complete #205.

## CI gate and branch protection verification — #207 / parent #200

The existing dependency install, full pytest/coverage/JUnit and both security
checks remain. Python Ruff is blocking after equivalent lint cleanup. Deploy
depends on `CI gate`; the provider helper requires a successful gate before
network calls. PyYAML is added to development dependencies for the workflow
contract test, not to production runtime requirements.

All new nodes are in `tests/test_ci_gate.py`:

| Mapping | Real function / variants | Result / dependency |
|---|---|---|
| CI207-01 | `test_required_ci_job_cannot_be_bypassed` (12 combinations: detection/Python/security × failure/cancelled/skipped/empty) | Required failed or missing jobs cannot become a green gate; #205 release contract |
| CI207-02 | `test_optional_stack_does_not_hide_failure` (6 combinations) | Optional absent Node may skip; detected failed/skipped Node and invalid detection fail closed |
| CI207-03 | `test_deploy_rejects_non_green_gate_before_provider_call` (4 variants: None/failure/cancelled/skipped) | Actual deploy helper refuses before a provider call |
| CI207-04 | `test_production_workflow_retains_full_suite_and_security_gate` | Parsed YAML preserves full suite/security scans/read-only token, always-run gate dependencies, main-push-only opt-in production deployment and secret isolation |
| CI207-05 | `test_current_approval_only_rules_are_not_reported_as_ci_protection` | Existing approval-only rules do not count as required named checks |
| CI207-06 | `test_required_checks_must_be_strict_and_from_actions` (3 variants) | Strict/up-to-date named checks require actual GitHub Actions App ID 15368 |
| CI207-07 | `test_non_admin_cannot_apply_ruleset` | No mutating request is made without verified administrator permission |

Existing `tests/test_deployment.py` nodes retain their real mount/bootstrap,
event/config/exact-SHA/readiness checks; the fake environment adds the gate's
success contract. Their positive fake-provider case is not a real hosted deploy.
No existing test was deleted, skipped or xfailed. The deliberate failure exists
only in closed, unmerged [rehearsal PR #231](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/231).

Actual local execution by OpenAI Codex (AI-assisted; not a teammate review),
Windows NT 10.0.26200.0 / Python 3.11.9 / pytest 9.2.0 / PyYAML 6.0.3 /
Playwright 1.65.2 / Chrome 157.0.8103.51:

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .venv/m4-env/Scripts/python.exe -m pytest -v --cov --cov-report=term-missing --junitxml=docs/evidence/207/pytest.xml
# 228 passed in 57.74s; zero failures/errors/skips
& .venv/m4-env/Scripts/python.exe -m ruff check .
# All checks passed!
```

[Full console](evidence/207/pytest.txt), [JUnit](evidence/207/pytest.xml).
Focused gate/deployment run: **38 passed in 0.32s**. `git diff --check` passes.

Real GitHub rehearsal: [run 43733767041](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43733767041)
reported **1 intentionally failed, 228 passed in 34.17s**, then aggregate gate
failure and production deploy skipped. The sole failure/node and actual job
links/log excerpts are in [red evidence](evidence/207/red-log-summary.json).
PR #231 is closed without merge; its red test is absent from this branch.

Latest observed main CI [43731613604](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43731613604)
at `6acf0dd` is green, **78s** from GitHub run-start to updated/completed time.
That historical run precedes this new gate. Administrator application/read-back
of named checks, an updated settings screenshot, independent approval and an
actual reviewed-green-main/provider release remain required external evidence;
local tests and the old screenshot do not certify these settings/actions.

## #190 / PR #227 merge reconciliation with main 6acf0dd

Resolved conflicts in `tests/test_backend_runtime.py` and
`tests/test_database_integrity.py` while preserving the #205 integration and
both sets of assertions. Backup tests retain main's requested mode-0600 check,
POSIX effective permissions and Windows read/write attributes, plus the full
restore/no-overwrite workflow. FK tests retain both the immediate and fresh
connection checks and the exact unchanged snapshot. Rollback tests retain the
trigger callback, sanitized 503, exact draft/new snapshot restoration and retry.
No test node, production behavior or approval policy is removed or bypassed.

Focused Windows/Python 3.11.9 verification:
`python -m pytest -q tests/test_backend_runtime.py tests/test_database_integrity.py`
returned **43 passed in 1.23s**; Ruff on both files and `git diff --check` passed.

Full run with the same installed Chrome override:
`python -m pytest -v --junitxml=docs/evidence/190/merge-pytest.xml` returned
**200 passed in 62.73s**, zero failures/errors/skips (190 retained + 10 merged
deployment cases). [Console](evidence/190/merge-pytest.txt) and
[JUnit](evidence/190/merge-pytest.xml) retain this integration result separately
from both earlier 190-case remediation and the original failing baseline.

## Health and sanitized monitoring verification - #206 (2026-11-15)

Parent #200; database #204 and deployed verification #205/#210. Reuses #223's
BE-01 healthy/missing/empty/corrupt nodes, BE-02 privacy and BE-04/10 failure
sanitization, rather than duplicating them. Operations procedure, arithmetic,
thresholds, owner and outstanding platform checks: [operations.md](operations.md).
The 97 story-case matrix remains separate from this monitoring coverage.

| ID | Real pytest node in tests/test_monitoring.py | Decision / result |
|---|---|---|
| MON-206-01 | `test_health_rejects_unusable_database[missing-table]` | Real isolated table loss -> sanitized 503; intact seed -> 200 |
| MON-206-02 | `test_health_rejects_unusable_database[orphan]` | Real isolated FK inconsistency -> sanitized 503; seed unchanged |
| MON-206-03 | `test_health_rejects_unusable_database[locked]` | Exclusive lock on isolated copy -> timeout/503; seed unchanged |
| MON-206-04 | `test_sanitized_correlated_error_and_duration` | Controlled 125ms/10ms, safe 500, per-request IDs and UTC time, no private input |
| MON-206-05 | `test_database_error_logs_are_correlated[/api/courses/1/feedback-application/json-database_unavailable]` | API DB 503 shares ID with completion/header; exception message absent |
| MON-206-06 | `test_database_error_logs_are_correlated[/lecturer/feedback/1-text/html-feedback_database_unavailable]` | HTML DB 503 shares ID with completion/header; exception message absent |
| MON-206-07 | `test_unrecognized_method_is_not_logged_as_user_input` | Unknown HTTP verb becomes OTHER in logs |
| MON-206-08 | `test_metric_threshold_boundaries[19-1-1001-False]` | Below 20-request minimum: low sample, no rate/latency breach |
| MON-206-09 | `test_metric_threshold_boundaries[20-0-1000-False]` | At sample minimum, 0% error and exactly 1000ms do not breach |
| MON-206-10 | `test_metric_threshold_boundaries[20-1-1000-True]` | Exactly 5% error breaches, latency at threshold does not |
| MON-206-11 | `test_metric_threshold_boundaries[20-1-1001-True]` | Above latency threshold breaches |
| MON-206-12 | `test_metric_window_filtering_and_nearest_rank` | Fixed UTC window edges, health/static exclusion, 4xx denominator, p95 rank, de-duplication |
| MON-206-13 | `test_metrics_ignore_bad_samples_without_echoing_input` | Bad/nonfinite and out-of-window input yields no invented values or leaked text |

Database fixtures use per-test temporary paths and controlled app time; lock/
corruption work only on copies. Duration tests mock monotonic time, metric tests
use explicit UTC instants. Config/environment, factories, views, logging and clock
patches restore through pytest fixtures. No production database is interrupted.

Main 686bd9e still contains stale #189 FK-OFF/escaping-exception expectations after
#223 fixed the runtime. This branch applies the same scoped reconciliation as
prepared #205: DB-189-F01 now requires FK=1 and actual orphan rejection on fresh
connections; rollback nodes assert sanitized 503, exact snapshot restoration and
successful retry. BE-05 uses a truly absolute tmp_path; BE-07 verifies requested
0600 creation and effective POSIX mode bits on POSIX, without claiming Windows ACL
privacy. All old cases are retained and no failing test is skipped.

Actual Windows / Python 3.12.6 / pytest 9.0.2 results:

```text
python -m pytest -q tests/test_monitoring.py tests/test_backend_runtime.py tests/test_database_integrity.py
56 passed in 8.52s

# Installed Chrome selected via PLAYWRIGHT_CHROMIUM_EXECUTABLE
python -m pytest -q --junitxml=junit.xml
203 passed in 135.44s (0:02:15)
```

JUnit: zero failures/errors/skips; 190 retained collected cases plus 13 monitoring
variants. Runtime/tool/changed test modules passed Ruff. `src/app.py` retains two
pre-existing SIM114/UP017 findings also reproduced from origin/main; changed imports
are formatted. `git diff --check` passed.

A real loopback HTTP rehearsal on a disposable schema-only DB produced
**200 -> 503 -> 200**; the missing DB was not created and the metric reducer counted
one health failure separately from the interactive denominator. See
[evidence](evidence/206/local-health.json) with actual UTC time, request IDs and
source hashes. This is local HTTP, not the public HTTPS release. A separate
[synthetic CLI summary](evidence/206/synthetic-metrics.json) verifies 20 generated
requests / one 503 -> 5% error, p95 950ms and exit 2; these are not observed
production values. Platform/service-specific log access, actual live health demo,
notification delivery and independent review remain pending in operations.md.

### #206 conflict resolution against main ef03d97

Merged #205 deployment setup and #190 M4 evidence without discarding either
README link or verification section. Retained main's stronger orphan snapshot,
trigger-reached rollback assertion and Windows backup checks; monitoring's extra
log fields remain asserted. No production behavior was changed for this merge.
Windows/Python 3.12.6: focused health/runtime/audit **56 passed in 13.79s**;
full suite with installed Chrome selected through PLAYWRIGHT_CHROMIUM_EXECUTABLE,
`python -m pytest -q --junitxml=junit.xml` -> **213 passed in 189.78s**, zero
failures/errors/skips. Changed runtime/tool/test Ruff and `git diff --check` passed.
Public deployment/live-monitoring evidence remains pending as described above.

## #204 / PR #229 reconciliation with main 83f76aa

Merged main's #190 remediation and #206 monitoring changes while preserving
the #204/#205 documentation and every dated run. The only Git conflict was
the introductory section of this document; both sets of evidence are retained.

The first integrated run returned **1 failed / 228 passed in 113.73s**:
`tests/test_production_database.py::test_seeded_submission_survives_browser_reload`
timed out waiting for the submit-confirmation button. The test called
`Locator.all()` without waiting for asynchronously fetched questions. It now
waits for the canonical seed's two rating questions and asserts each selected
radio is checked before review. No sleeps, retries, skipped tests or weaker
persistence assertions were introduced. Focused verification returned
**1 passed in 4.41s** on Windows/Python 3.11.9 with installed Chrome.

[Initial console](evidence/204/merge-first-pytest.txt) and
[JUnit](evidence/204/merge-first-pytest.xml) retain the timeout result, separately
from the final rerun. Database/backup tests, role login, exact persisted rows,
new-process preservation and restored workflows remain unchanged.

The next full run returned **1 failed / 228 passed in 87.77s** in the existing
`tests/test_p0_browser_contracts.py::test_logout_navigates_to_login[phone]`:
Review was clicked before fetched questions existed, so the expected missing-
answer validation was not shown. This test now waits for the fixture's single
rating question before exercising empty-answer validation. The validation,
keyboard selection, submit, reload, persistence and logout assertions are all
retained. [Second console](evidence/204/merge-second-pytest.txt) and
[JUnit](evidence/204/merge-second-pytest.xml) preserve that run. Focused execution
of both laptop/phone variants plus the canonical-seed reload test returned
**3 passed in 11.55s**. These are test precondition/synchronization changes;
production loading behavior is unchanged.

Final Windows/Python 3.11.9 full execution, using installed Chrome through
`PLAYWRIGHT_CHROMIUM_EXECUTABLE`:
`python -m pytest -v --junitxml=docs/evidence/204/merge-pytest.xml` returned
**229 passed in 78.53s**, no failures/errors/skips (213 retained main cases +
16 #204 cases). [Final console](evidence/204/merge-pytest.txt) and
[JUnit](evidence/204/merge-pytest.xml) retain the result. Changed Python module
Ruff and `git diff --check` passed. No production schema/storage or health/log
behavior was changed by this merge resolution.

## P0 / M4 release rehearsal - #210 (2026-11-15)

Parent #200 and dependencies #201/#202/#205/#206/#209. The focused register,
existing normal/error/applicable boundary nodes, public-step results and limits
are in [p0-release-verification.md](p0-release-verification.md). No duplicate
wrong-password/unknown-email or other existing pytest test is added.

Actual candidate main `6acf0dd` local Windows/Python 3.12.6 run with installed
Chrome: `python -m pytest -q --junitxml=junit.xml` -> **200 passed in 173.05s**,
zero failures/errors/skips. This includes existing student/lecturer browser flows,
receipt reload/persistence, server rejection/recovery, logout and database-aware
health checks. It is not public HTTPS / physical-phone or hosted rollback proof.
[Per-module evidence](evidence/210/main-6acf0dd-local.json).

A prior pinned main `ebb938d` run had **5 failed / 185 passed in 152.65s**;
[that report](evidence/210/main-ebb938d-local.json) is retained. #226 merged the
previously prepared test reconciliations while this audit ran; the newer green
candidate does not erase or relabel the historical failed result.

`python tools/rehearse_business_rule.py --revision 6acf0dd` executed the existing
`tests/test_student_evaluations.py::test_student_evaluations_due_soon_24_hour_boundary`
in a temporary git export: baseline **3 passed**, strict `<24h` changed to `<=24h`
-> **1 failed / 2 passed** (only TC-09-at), original bytes restored -> **3 passed**.
[Actual output/hashes](evidence/210/mutation.json) confirm the workspace source was
unchanged. The defect was never committed or deployed. The earlier ebb938d
rehearsal is separately preserved. This is a controlled mutation demonstration,
not a new production fix or fabricated red-test screenshot.

Public origin/provider SHA, real private desktop/physical phone, released
business rejection, live health/rollback and deployed visible-outcome timings
remain pending. A PR closing reference must not be used to merge/close #210
before those verification gates and independent recorded review are satisfied.

### #210 merge verification against main e5564f7

Resolved the docs/testing.md append conflict by preserving #190 M4 review,
#204 database, #205 deployment, #206 monitoring and #210 rehearsal evidence.
Production/test code was not changed for this resolution. Existing dated reports
remain intact; the current candidate register and CI link now point to e5564f7.

Windows/Python 3.12.6 with installed Chrome:
`python -m pytest -q --junitxml=junit.xml` -> **229 passed in 162.18s**, zero
failures/errors/skips. [Per-module result](evidence/210/main-e5564f7-local.json).
`python tools/rehearse_business_rule.py --revision e5564f7 --output docs/evidence/210/mutation-e5564f7.json`
-> baseline **3 passed**, mutant **1 failed / 2 passed** (TC-09-at only), restored
**3 passed**; source/workspace hashes unchanged after restoration.
[Rehearsal output](evidence/210/mutation-e5564f7.json). Script Ruff and
`git diff --check` passed. Public URL/provider SHA, physical phone and hosted
rollback remain unverified; local/CI results do not complete those gates.

## #207 / PR #232 integration with main 55e81b5

Resolved both `docs/testing.md` conflict blocks by retaining #207's gate and
protection evidence alongside main's #190, #204, #205, #206 and #210 results.
Main's database/browser synchronization, monitoring and P0 rehearsal changes
are included. The full-suite/security requirements, blocking Ruff, stable
`CI gate` and main-only deployment dependency remain unchanged.

Windows/Python 3.11.9 / pytest 9.2.0, installed Chrome:

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .venv/m4-env/Scripts/python.exe -m pytest -v --cov --cov-report=term-missing --junitxml=docs/evidence/207/merge-pytest.xml
# 257 passed in 76.11s; zero failures/errors/skips
& .venv/m4-env/Scripts/python.exe -m ruff check .
# All checks passed!
```

[Integrated console](evidence/207/merge-pytest.txt) and
[JUnit](evidence/207/merge-pytest.xml) retain all 229 merged main cases plus
28 CI/protection cases. Original 228-case reports and the closed red rehearsal
remain historical evidence. `git diff --check` passed. This merge does not
apply administrator rules, grant approval, certify a provider release or
replace the outstanding administrator/release handoff.

## US13 creation verification - #198 (2026-11-16)

Parent #193 (P1), shared US08 #38/#40, frontend #197 and queries #199. The existing
POST /api/evaluations is extended, not duplicated. [Full contract/profile](lecturer-creation-api.md).
The 97 P0 matrix remains separate from these P1 cases.

| Trace ID | Actual node in tests/test_evaluation_creation.py | Decision |
|---|---|---|
| US13-01 | `test_creation_question_count[questions-0]` | Reject empty questions, no writes |
| US13-02 | `test_creation_question_count[questions-1]` | One question allowed, exact course/creator/ordered persistence |
| US13-03 | `test_creation_question_count[questions-5]` | Exactly five stored and returned as display data |
| US13-04 | `test_creation_question_count[questions-6]` | Five is not a maximum |
| US13-05 | `test_creation_denies_invalid_actor[None-401]`, `[1-403]`, `[999-401]` | Anonymous/Student/deleted actor cannot create despite body/query identity claims |
| US13-06 | `test_unassigned_creation_exact_message_and_no_writes` | Assignment to course1 does not authorize course2; exact required denial |
| US13-07 | `test_administrator_creation_reuses_us08_without_course_assignment` | Shared endpoint preserves US08 management role |
| US13-08 | `test_invalid_creation_has_no_writes` (10 variants: title/missing-deadline/bad-deadline/bad-course/missing-course/missing-questions/question-type/required-type/question-object/question-text) | Validate without partial records; canonical US08 missing deadline message |
| US13-09 | `test_question_failure_rolls_back_evaluation_and_prior_question` | Real second-question ABORT reached after first insert; rollback + retry |

Twenty new variants use the real schema, Flask test client, temporary SQLite and
existing fixed clock. Existing #40 smoke tests are retained. Actual Windows/
Python 3.12.6: focused `python -m pytest -q tests/test_evaluation_creation.py tests/test_smoke.py`
-> **55 passed in 8.90s**; full `python -m pytest -q --junitxml=junit.xml` with
installed Chrome -> **277 passed in 154.68s**, no failures/errors/skips.
The ownership test was strengthened for selected-course isolation and the focused
suite passed again. Repository Ruff and diff checks passed. [Module counts](evidence/198/local-tests.json).

Real latency is measured separately with `python -m tools.measure_creation_latency
--samples 30 --warmups 3`: local loopback HTTP, one sequential preauthenticated
lecturer, five questions, existing synthetic P0 data profile. **p50 17.488ms,
p95 20.084ms, maximum 20.853ms**, 30/30 HTTP201 confirmations and persisted values
verified; all <=3000ms on this profile. [Raw samples/environment/source hashes](evidence/198/creation-latency.json).
This does not certify deployed/browser visible confirmation or use pytest runtime
as latency. Frontend #197 and independent #199 review remain pending; no UI,
production data change or public latency result is fabricated.
