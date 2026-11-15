# EduSurvey M4 Automated Testing

## 1. What we test, and why

Evidence reviewed on 2026-11-15 for Issue #164: `docs/requirements.md`, `docs/design.md`, `docs/SETUP.md`, `docs/sprint-log.md`, README, all six test modules, `src/app.py`, `src/schema.sql`, `src/status.py`, `src/feedback_queries.py`, and the templates/static scripts. `docs/ui.md` was inspected as an existing **untracked local draft**; it is not a fresh-clone dependency. Remote `main` was fetched and inspected at `fa13dd1`; this branch starts at `759669f`, which adds a README change above main. Application and test sources match fetched main. Unrelated local README, CSS, template, backup and ZIP changes are excluded from this deliverable.

| Layer | What is tested | Technique | Reason / limitations |
|---|---|---|---|
| Services / business logic | Status precedence, deadlines, topic classification; submission validation inside route functions | Unit tests in `test_status.py` and `test_feedback_classifier.py`; equivalence partitions and boundary analysis through API tests | Most business logic remains in `src/app.py`, rather than separate service classes. The standalone status helper and route duplicate logic, so both require coverage. |
| Repository / database | Response and answer uniqueness, submission timestamp storage, queries excluding drafts and unrelated evaluations | In-memory SQLite schema tests; integration tests against `tmp_path` databases | Protects integrity and feedback accuracy. SQL is primarily inline in routes; no general repository abstraction exists. Foreign keys are enabled in schema tests; production `get_db_connection()` does not explicitly enable them, so full runtime FK enforcement is not established. |
| Flask routes / API | Authentication, student role/enrollment, required answers, deadlines, duplicates, lecturer ownership and logout | Flask test client; temporary databases; positive/negative partitions and fixed-time boundary tests where implemented | Exercises request, session, validation and SQL together without starting a server. Successful submission persistence and several exact boundaries remain unautomated. |
| User interface | Basic HTML rendering and student page role restrictions | Flask rendering smoke tests; manual browser review still needed | No browser automation exists for JavaScript validation, redirects, accessibility or responsive layout. Lecturer feedback and sign-out UI gaps must not be reported as tested. |

Authentication and authorization receive priority because a role or course-ownership error could expose student feedback. Submission validation, exact deadlines and duplicate prevention protect irreversible response data; database constraints and lecturer filtering provide additional safeguards. A green suite demonstrates only its assertions, not complete acceptance-criteria coverage.

## 2. Test cases for every P0 story

The backlog table and story acceptance criteria in [requirements.md](requirements.md) confirm exactly five P0 stories: **US01 User Login and Authentication; US02 View Available Course Evaluations; US03 Complete and Submit Course Evaluation; US04 Review Submitted Student Feedback; US11 User Sign Out**.

Inputs below describe the implementation contract. HTTP errors use `error.code` and `error.message`. Messages shown are verified from source; an existing test may assert only the status/code, as detailed in Section 3. A pending case is a specification derived from source, not execution evidence.

For new tests, use a separate temporary SQLite database per case, load `src/schema.sql`, seed an enrolled student and assigned lecturer, and freeze `src.app.datetime` at T=2026-11-03T12:00:00 unless another instant is specified. Fresh submissions must have no pre-existing submitted response; delete answers before deleting the seeded response. Never initialize or read `data/edusurvey.db`. Existing tests retain their own fixtures and time limitations described in Section 3.

| ID | Story | Input | Expected result | Kind |
|---|---|---|---|---|
| TC-01 | US01 | POST /api/auth/login; student1@edusurvey.edu / Password123! | 200; authenticated=true; student role; no password_hash | Normal |
| TC-02 | US01 | Same email; password=wrong-password | 401; INVALID_CREDENTIALS; "Email or password is incorrect." | Error |
| TC-03 | US01 | unknown@edusurvey.edu / Password123! | 401; INVALID_CREDENTIALS | Error |
| TC-04 | US01 | Known email; omit password | 400; MISSING_CREDENTIALS; "Email and password are required." | Error |
| TC-05 | US02 | Student 1 enrolled in course 1; GET /api/evaluations; three open/closed evaluations | 200; count=3; Course Feedback has title, course, lecturer, deadline and Active status | Normal |
| TC-06 | US02 | Anonymous GET /api/evaluations | 401; UNAUTHORIZED | Error |
| TC-07 | US02 | Lecturer GET /api/evaluations | 403; FORBIDDEN | Error |
| TC-08 | US02 | Student 1; T=2026-11-03T12:00:00; deadline=T+23h59m | 200; Due soon | Boundary |
| TC-09 | US02 | Same T; deadline=T+24h | 200; Active | Boundary |
| TC-10 | US02 | Same T; deadline=T+24h1s | 200; Active | Boundary |
| TC-11 | US02 | Same T; open evaluation; deadline=T-1s | 200; Closed | Boundary |
| TC-12 | US02 | Same T; open evaluation; deadline=T | 200; Closed | Boundary |
| TC-13 | US02 | Same T; open evaluation; deadline=T+1s | 200; Due soon | Boundary |
| TC-14 | US03 | Enrolled student; fresh open evaluation 1; future deadline; required rating question 1; POST /api/submissions with evaluation_id=1, answers={"1":{"rating_value":5}} | 201; status=submitted; one response and answer persisted; "Evaluation submitted successfully." | Normal |
| TC-15 | US03 | Student session; POST /api/submissions with evaluation_id=1, answers={} | 400; MISSING_REQUIRED_ANSWERS; "Please answer all required questions before submitting." | Error |
| TC-16 | US03 | Existing submitted response for student 1/evaluation 1; valid_payload() | 409; DUPLICATE_SUBMISSION; "You have already submitted this evaluation." | Error |
| TC-17 | US03 | Anonymous; valid submission payload | 401; UNAUTHORIZED | Error |
| TC-18 | US03 | Fresh response; valid answers; deadline D=2026-11-04T12:00:00; frozen now=D-1s | 201; status=submitted | Boundary |
| TC-19 | US03 | Fresh response; valid answers; deadline D=2026-11-04T12:00:00; frozen now=D0s | 400; DEADLINE_EXPIRED; "The submission deadline has passed." | Boundary |
| TC-20 | US03 | Fresh response; valid answers; deadline D=2026-11-04T12:00:00; frozen now=D+1s | 400; DEADLINE_EXPIRED; "The submission deadline has passed." | Boundary |
| TC-21 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=0 | 400; INVALID_RATING; "Rating must be an integer between 1 and 5." | Boundary |
| TC-22 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=1 | 201; rating persisted unchanged | Boundary |
| TC-23 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=2 | 201; rating persisted unchanged | Boundary |
| TC-24 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=4 | 201; rating persisted unchanged | Boundary |
| TC-25 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=5 | 201; rating persisted unchanged | Boundary |
| TC-26 | US03 | Fresh response; open evaluation; frozen T; deadline=T+2 days; required rating_value=6 | 400; INVALID_RATING; "Rating must be an integer between 1 and 5." | Boundary |
| TC-27 | US03 | Fresh response; required rating=5; optional text question 2; text_value="a" repeated 1999 times; future deadline at frozen T | 201; text of length 1999 persisted | Boundary |
| TC-28 | US03 | Fresh response; required rating=5; optional text question 2; text_value="a" repeated 2000 times; future deadline at frozen T | 201; text of length 2000 persisted | Boundary |
| TC-29 | US03 | Fresh response; required rating=5; optional text question 2; text_value="a" repeated 2001 times; future deadline at frozen T | 400; TEXT_TOO_LONG; "Text answers cannot exceed 2000 characters." | Boundary |
| TC-30 | US03 | Exactly 5 required rating questions; answer 4 with rating=3; fresh response; deadline=T+2 days at frozen T | 400; MISSING_REQUIRED_ANSWERS; no response persisted | Error |
| TC-31 | US03 | Exactly 5 required rating questions; answer 5 with rating=3; fresh response; deadline=T+2 days at frozen T | 201; exactly one submitted response with 5 answers | Normal |
| TC-32 | US04 | Lecturer 2 assigned to course 1; GET /api/courses/1/feedback; one submitted response, rating=5 and comment="The course content was very useful." | 200; completed_evaluations=1; returned rating and text match | Normal |
| TC-33 | US04 | Lecturer 4 without course assignment; GET /api/courses/1/feedback | 403; FORBIDDEN; "You do not have permission to view this course feedback." | Error |
| TC-34 | US04 | Student session; GET /api/courses/1/feedback | 403; FORBIDDEN | Error |
| TC-35 | US04 | Anonymous GET /api/courses/1/feedback | 401; UNAUTHORIZED | Error |
| TC-36 | US04 | Assigned lecturer; course 1 has one submitted and one draft response | 200; completed_evaluations=1; draft excluded | Normal |
| TC-37 | US04 | Assigned lecturer; 20 distinct students each have one submitted response in course 1 | 200; completed_evaluations=20; 20 responses | Normal |
| TC-38 | US11 | Login with student1@edusurvey.edu / Password123!; POST /api/auth/logout; GET /api/auth/me using the same client | GET returns 401 after logout; logout implementation returns 200, authenticated=false | Normal |
| TC-39 | US11 | Student logs out; GET /api/evaluations using the now-cleared client session | 401; UNAUTHORIZED; no evaluation data | Error |
| TC-40 | US11 | Lecturer logs out; GET /api/courses/1/feedback with cleared session | 401; UNAUTHORIZED; no feedback | Error |
| TC-41 | US11 | Anonymous POST /api/auth/logout twice | Both 200; authenticated=false; no redirect | Normal |

The Due soon rule is strictly less than 24 hours, with deadline equality already Closed. The existing API boundary test covers 23h59m, 24h, **25h** and 12h; it does not cover the immediately-above case 24h1s. Rating boundaries cover 0/1/2 and 4/5/6; text boundaries apply after trimming and cover 1999/2000/2001 characters. Five required answers and 20 completed responses are acceptance examples, not hard-coded maxima: there is no five-question or twenty-response limit in the implementation.

Requirements differ from the current contract: login expects "Invalid email or password." while code returns "Email or password is incorrect."; duplicate submission expects "You have already completed this evaluation." while code says "You have already submitted this evaluation."; requirements capitalize "Due Soon" while code returns "Due soon". Logout returns JSON and protected pages return 401 JSON, rather than the specified redirect. These are unresolved acceptance gaps, not approved requirement changes. The three-second response-time requirement has no automated performance test; suite elapsed time is not latency evidence. Boundary performance measurements require a controlled load/environment and an agreed timing contract.

## 3. Automated tests

From the repository root, use Python 3.12 (the CI version; the setup guide currently suggests 3.14):

```bash
python -m venv .venv
source .venv/bin/activate
# Windows activation: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install pytest==7.4.4
python -m pytest -v
```

`requirements.txt` pins Flask 3.1.2 but does not include pytest. CI installs pytest separately and invokes coverage; no Flask process or database initialization command is needed to run these tests. Dependency installation from a new clone was not executed in this review.

For a single mapping below, run `python -m pytest -v path/to/test_file.py::test_function`; for example:

```bash
python -m pytest -v tests/test_auth.py::test_login_success
python -m pytest -v tests/test_student_evaluations.py::test_student_evaluations_due_soon_24_hour_boundary
```

All existing mappings below are API integration tests using temporary SQLite databases and Flask's test client. Expected results are specified by the matching Section 2 ID; **PASS** means the existing function passed, not that every source-derived detail in Section 2 is asserted. **NOT IMPLEMENTED** means no corresponding test exists, no function name is proposed as if real, and no pass is claimed.

| Case ID | Pytest function | File | Level / type | Expected / actual verified result | Responsible Sprint 4 task |
|---|---|---|---|---|---|
| TC-01 | `test_login_success` | `tests/test_auth.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #165 |
| TC-02 | `test_login_wrong_password` | `tests/test_auth.py` | API integration / error | Section 2 expectation; existing assertions PASS | #165 |
| TC-03 | `test_login_unknown_email` | `tests/test_auth.py` | API integration / error | Section 2 expectation; existing assertions PASS | #165 |
| TC-04 | `test_login_missing_password` | `tests/test_auth.py` | API integration / error | Section 2 expectation; existing assertions PASS | #165 |
| TC-05 | `test_student_evaluations_success` | `tests/test_student_evaluations.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #166 |
| TC-06 | `test_student_evaluations_requires_login` | `tests/test_student_evaluations.py` | API integration / error | Section 2 expectation; existing assertions PASS | #166 |
| TC-07 | `test_student_evaluations_forbidden_for_lecturer` | `tests/test_student_evaluations.py` | API integration / error | Section 2 expectation; existing assertions PASS | #166 |
| TC-08 | `test_student_evaluations_due_soon_24_hour_boundary` | `tests/test_student_evaluations.py` | API integration / boundary | Section 2 expectation; existing assertions PASS | #166 |
| TC-09 | `test_student_evaluations_due_soon_24_hour_boundary` | `tests/test_student_evaluations.py` | API integration / boundary | Section 2 expectation; existing assertions PASS | #166 |
| TC-10 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #166 |
| TC-11 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #166 |
| TC-12 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #166 |
| TC-13 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #166 |
| TC-14 | NOT IMPLEMENTED | — | Planned API integration / normal | Section 2 expectation; NOT RUN | #167 |
| TC-15 | `test_submission_missing_required_answers` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #167 |
| TC-16 | `test_duplicate_submission` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #167 |
| TC-17 | `test_submission_requires_login` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #167 |
| TC-18 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-19 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-20 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-21 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-22 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-23 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-24 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-25 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-26 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-27 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-28 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-29 | NOT IMPLEMENTED | — | Planned API integration / boundary | Section 2 expectation; NOT RUN | #167 |
| TC-30 | NOT IMPLEMENTED | — | Planned API integration / error | Section 2 expectation; NOT RUN | #167 |
| TC-31 | NOT IMPLEMENTED | — | Planned API integration / normal | Section 2 expectation; NOT RUN | #167 |
| TC-32 | `test_lecturer_can_retrieve_course_feedback` | `tests/test_smoke.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #168 |
| TC-33 | `test_lecturer_cannot_access_unassigned_course` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #168 |
| TC-34 | `test_student_cannot_access_lecturer_feedback` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #168 |
| TC-35 | `test_course_feedback_requires_login` | `tests/test_smoke.py` | API integration / error | Section 2 expectation; existing assertions PASS | #168 |
| TC-36 | `test_course_feedback_count_excludes_draft_responses` | `tests/test_smoke.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #168 |
| TC-37 | NOT IMPLEMENTED | — | Planned API integration / normal | Section 2 expectation; NOT RUN | #168 |
| TC-38 | `test_logout_clears_session` | `tests/test_auth.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #169 |
| TC-39 | NOT IMPLEMENTED | — | Planned API integration / error | Section 2 expectation; NOT RUN | #169 |
| TC-40 | NOT IMPLEMENTED | — | Planned API integration / error | Section 2 expectation; NOT RUN | #169 |
| TC-41 | NOT IMPLEMENTED | — | Planned API integration / normal | Section 2 expectation; NOT RUN | #169 |

Traceability totals: **41 cases; 18 mapped to existing tests; 23 NOT IMPLEMENTED**. One existing boundary function maps to two cases, so case counts are not pytest collection counts.

| Story | Documented cases | Existing mappings | Pending |
|---|---:|---:|---:|
| US01 | 4 | 4 | 0 |
| US02 | 9 | 5 | 4 |
| US03 | 18 | 3 | 15 |
| US04 | 6 | 5 | 1 |
| US11 | 4 | 1 | 3 |

**Actual local execution, 2026-11-15:** `python -m pytest -v` on macOS, Python 3.12.4, pytest 7.4.4, anyio 4.2.0; exit 0:

```text
collected 63 items
============================== 63 passed in 3.32s ==============================
```

All six modules ran: `test_auth.py` (7), `test_feedback_classifier.py` (3), `test_response_schema.py` (3), `test_smoke.py` (35), `test_status.py` (6), and `test_student_evaluations.py` (9). The extra tests cover schema integrity, classification, statistics, evaluation creation/deadline updates and reminders beyond the case matrix. There is no screenshot or verified CI result for this documentation commit.

**Fixture and assertion audit / remaining work:**

- #165: `test_auth.py` creates a minimal users table and hashes a test-only password. Login success checks the student role and password-hash exclusion; failure-message equality, lecturer/admin login and unsupported roles need additional assertions/tests.
- #166: list fixtures use `datetime.now()` to seed relative dates. The 24-hour boundary function freezes the route clock but not fixture setup; freeze time before fixture creation for full reproducibility. The normal list test asserts three total evaluations (including a closed one), not the requirements example of three active evaluations.
- #167: smoke fixtures pre-seed a submitted response, so current submission tests cover rejection rather than a successful submission. Use fresh/draft data for success and boundary cases. The existing expired-deadline test uses 2000, while normal fixtures use 2099 and the real clock; neither is an exact fixed-time boundary. Test transaction rollback, enrollment/role denial, question loading at `GET /api/evaluations/<evaluation_id>/questions`, invalid IDs and wrong-question answers as further coverage. Required-answer and duplicate error messages come from source; existing tests assert codes only.
- #168: lecturer ownership denial asserts the exact message. Other mapped feedback tests assert status and/or returned data. Add the 20-response acceptance example and test no cross-course leakage. Statistics and topic routes currently lack the authentication/ownership decorators used by the course-feedback route; passing smoke tests do not establish access control for those endpoints.
- #169: logout test asserts only that subsequent `/api/auth/me` returns 401. It does not assert the logout response body, redirects, role-specific denial or replay of a saved pre-logout cookie. Flask uses a signed client-side cookie and logout calls `session.clear()`; server-side revocation of a copied old cookie is not demonstrated. Shared app configuration is changed by fixtures without comprehensive restoration; centralize isolated fixtures and freeze both Python time and SQL timestamps where assertions depend on time.

Schema tests explicitly enable foreign keys on `:memory:` SQLite. Smoke tests load the real schema into `tmp_path`; other fixtures create reduced schemas, so they cannot establish all production constraints. Some smoke fixture rows use SQLite `CURRENT_TIMESTAMP`, which Python clock patching does not control. Current tests avoid the real application database, but the suite does **not yet satisfy** the stricter requirement to avoid uncontrolled current dates everywhere. No existing tests or application logic were changed for this documentation task.

## 4. What the tests found

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
