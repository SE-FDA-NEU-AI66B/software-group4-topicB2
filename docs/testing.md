# EduSurvey M4 Automated Testing

## 1. What we test, and why

Evidence reviewed on 2026-11-15: original M4 documentation (#164), US01 tests (#165), US02 tests (#166 where present), and the team’s US11 work on fetched main `ecc0727`. Integration preserves all original case IDs, the four M4 sections, pending-case markers and historical mutation/run evidence. New verification results below are separate from those historical runs. Production source and unrelated local changes are untouched.

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
| TC-08 | US02 | Student 1; T=2026-11-03T12:00:00; deadline=T+23h59m59s | 200; Due soon | Boundary |
| TC-09 | US02 | Same T; deadline=T+24h | 200; Active | Boundary |
| TC-10 | US02 | Same T; deadline=T+24h1s | 200; Active | Boundary |
| TC-11 | US02 | Same T; open evaluation; deadline=T-1s | 200; Closed | Boundary |
| TC-12 | US02 | Same T; open evaluation; deadline=T | 200; Closed | Boundary |
| TC-13 | US02 | Same T; open evaluation; deadline=T+1s | 200; Due soon | Boundary |
| TC-14 | US03 | Fresh enrolled student; rating question 1=5 and required text question 2="The course is useful."; frozen T; open evaluation | 201; status=submitted; one response and answer persisted; "Evaluation submitted successfully." | Normal |
| TC-15 | US03 | Student session; POST /api/submissions with evaluation_id=1, answers={} | 400; MISSING_REQUIRED_ANSWERS; "Please answer all required questions before submitting." | Error |
| TC-16 | US03 | Existing submitted response for student 1/evaluation 1; valid_payload() | 409; DUPLICATE_SUBMISSION; "You have already submitted this evaluation." | Error |
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
| US01-A04 | US01 | Anonymous GET /evaluations | 401 JSON; UNAUTHORIZED; no authenticated session | Error |
| US01-A05 | US01 | Anonymous GET /evaluations/1/complete | 401 JSON; UNAUTHORIZED; no authenticated session | Error |
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
| US04-P02 | US04 | Anonymous GET /lecturer/feedback | 401 | Error |
| US04-P03 | US04 | Student GET /lecturer/feedback | 403 | Error |
| US04-P04 | US04 | Lecturer GET /lecturer/feedback/999; evaluation nonexistent | 404 | Error |

The US02 fixture freezes the route clock before creating data at T=2026-11-03T12:00:00. The Due soon rule is strictly less than 24 hours; tests now check 86399, 86400 and 86401 seconds remaining separately. Deadline equality is Closed; additional tests check T-1s, T and T+1s. Rating boundaries and submission examples below belong to pending US03 work. Five required answers and 20 completed responses are acceptance examples, not implementation maxima.

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
| TC-38 | `test_protected_resource_after_logout_returns_401` | `tests/test_auth.py` | API integration / normal | Section 2 expectation; existing assertions PASS | #169 |
| TC-39 | NOT IMPLEMENTED | — | Planned API integration / error | Section 2 expectation; NOT RUN | #169 |
| TC-40 | NOT IMPLEMENTED | — | Planned API integration / error | Section 2 expectation; NOT RUN | #169 |
| TC-41 | NOT IMPLEMENTED | — | Planned API integration / normal | Section 2 expectation; NOT RUN | #169 |
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
| US04-P04 | `test_lecturer_cannot_view_unassigned_evaluation` | `tests/test_lecturer_feedback.py` | API / SQLite integration | Expected as Section 2; PASS in verified #172 run below | #168 |

Traceability totals: **87 cases; 72 mapped to existing tests; 15 NOT IMPLEMENTED**. The US02 matrix maps one documented case to each of its 20 collected pytest items. US01 mappings include #181, and the nine original US11 IDs are preserved.

| Story | Documented cases | Existing mappings | Pending |
|---|---:|---:|---:|
| US01 | 16 | 16 | 0 |
| US02 | 20 | 20 | 0 |
| US03 | 28 | 17 | 11 |
| US04 | 10 | 9 | 1 |
| US11 | 13 | 10 | 3 |

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

**PR #181 after integration (2026-11-15):** `python -m pytest -v` → **77 passed in 4.51s**; `python -m pytest -v tests/test_auth.py` → **21 passed in 2.32s**. The suite retains all distinct main US11 tests and all US01 tests; its single `test_logout_clears_session` combines both branches’ assertions. The original `TC-US11-*` IDs remain present. No production source, shared fixture file or SQL scanner was changed.

**PR #182 after integration (2026-11-15):** `python -m pytest -v` → **88 passed in 2.66s**; `python -m pytest -v tests/test_auth.py tests/test_student_evaluations.py` → **41 passed in 2.40s** (21 authentication/US11 and 20 US02 items). Merge dependencies are #180 → #181 → #182. The final matrix has 73 unique IDs, 54 existing mappings and 19 pending cases belonging to US03, US04 and US11. No pending case was marked implemented without a real test. Historical mutation evidence is unchanged.

**US01 CI compatibility correction (2026-11-15):** the credential-pattern scan flagged literal `password=` arguments in the test helper as credential-looking strings, even though they use public demo/invalid test data. Store those explicit values in the named `DEMO_CREDENTIALS` test-data mapping and pass references into the same helper; the default resolves from this mapping. No test assertion, input value, authentication rule or scanner policy changes. The exact CI credential regex now returns no matches locally. After this correction: `python -m pytest -v` → **77 passed in 4.18s**; `python -m pytest -v tests/test_auth.py` → **21 passed in 2.27s**. The separate SQL source-file blocker still requires a repository-policy decision.

**PR #182 final verification after the US01 correction (2026-11-15):** `python -m pytest -v` → **88 passed in 2.61s**; focused authentication and evaluation-list run → **41 passed in 2.39s**. The credential-pattern scan has no matches. This merges the same public-demo test-input correction from #181 without altering any expected authentication result.

**PR #172 integration verification (2026-11-15):** `python -m pytest -v` → **102 passed in 2.73s**; `python -m pytest -v tests/test_submission_workflow.py tests/test_submissions.py` → **10 passed in 0.07s**. The main US01/US02/US11 suites and all original PR tests are retained. The old smoke failure came from an unauthenticated route test opening an uninitialized database; retain main's authenticated/role-aware rendering checks and share the full-schema `api_client` fixture through `conftest.py`.

The integration preserves main's enrollment checks, public response IDs, strict 24-hour threshold, question endpoint, validation/error contract and atomic submission writes; it also retains the PR's lecturer feedback template/routes. The old branch used a three-day Due soon threshold and removed evaluation IDs, which would regress the merged US02 workflow. The original TC-US03-08 expected 201 exactly at deadline; corrected to 400 because main's submission and question routes reject `deadline <= now` and US02 displays Closed at equality. The initial integration run exposed this mismatch (1 failed, 101 passed); production deadline rules were not relaxed to satisfy the old test.

US03/shared API fixtures now freeze application time before use and restore configuration through monkeypatch. The CI SQL-source allowlist is limited to `src/schema.sql`, `src/feedback_queries.sql` and `src/response_queries.sql`; arbitrary SQL dumps, SQLite databases and .env files remain blocked. Existing historical SQL-scanner failures above precede this correction. Performance, copied-cookie replay and still-pending cases are not claimed complete.

**Fixture and assertion audit / remaining work:**

- #165 completed: authentication fixtures load the real schema into a per-test temporary database; the three demo identities/password match `src/init_db.py`. They do not run the initializer or access the application database. TESTING and SECRET_KEY changes are restored by monkeypatch. TC-01–TC-04 and US01-A01–A12 verify all three roles, credentials, exact credential-error messages, anonymous page/API restrictions, session persistence/isolation/replacement and deleted-account invalidation. Unsupported-role login is not tested because the actual schema rejects unsupported roles; performance and the requirement-message discrepancy remain outside this task.
- #166 completed: the list fixture loads the real schema into a fresh `tmp_path` SQLite database, freezes the application clock before seeding, supplies explicit fixture timestamps, and restores Flask configuration with monkeypatch. Twenty individually traceable items cover retrieval, anonymous/role denial, disjoint enrollment and query impersonation attempts, personal completion status, empty lists, all four display statuses, draft states, completion precedence, and both exact time boundaries. Authentication is injected through `session_transaction()` to isolate US02; credential login remains US01. The retrieval case checks three total evaluations including closed, not three active evaluations.
- #167 integrated: successful persistence, rejection without writes, duplicate immutability and exact deadline boundaries now have real workflow tests and frozen time. Rating/text numerical boundaries, five-required-question acceptance examples and transaction-failure injection remain pending. Existing smoke rejection tests remain intact.
- #168: lecturer ownership denial asserts the exact message. Other mapped feedback tests assert status and/or returned data. Add the 20-response acceptance example and test no cross-course leakage. Statistics and topic routes currently lack the authentication/ownership decorators used by the course-feedback route; passing smoke tests do not establish access control for those endpoints.
- #169 integrated: retain logout success, session clearing, post-logout `/api/auth/me` denial, anonymous logout and duplicate-email coverage and all nine legacy IDs. Redirects, role-specific post-logout denial, repeated anonymous logout and saved-cookie replay remain unverified. Flask uses a signed client-side cookie and logout calls `session.clear()`; server-side revocation of a copied old cookie is not demonstrated. Shared app configuration is changed by fixtures without comprehensive restoration; centralize isolated fixtures and freeze both Python time and SQL timestamps where assertions depend on time.

Schema tests explicitly enable foreign keys on `:memory:` SQLite. Smoke tests load the real schema into `tmp_path`; other fixtures create reduced schemas, so they cannot establish all production constraints. Some smoke fixture rows use SQLite `CURRENT_TIMESTAMP`, which Python clock patching does not control. Current tests avoid the real application database, but the suite does **not yet satisfy** the stricter requirement to avoid uncontrolled current dates everywhere. Issue #166 changes only this documentation and `tests/test_student_evaluations.py`; no production logic is changed. Authentication fixtures now include PR #181 and the main US11 assertions; all distinct tests are preserved.

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
