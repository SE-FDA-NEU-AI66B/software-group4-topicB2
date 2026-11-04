## US03 – Course Evaluation Submission

### Test Cases

| Test Case ID | Test Scenario | Expected Result | Status |
|---|---|---|---|
| TC-US03-01 | Submit an evaluation with all required answers | Submission is successful (201). Response and answers are persisted in the database. | Passed |
| TC-US03-02 | Submit an evaluation with missing required answers | Request is rejected with 400. No submission records are created. | Passed |
| TC-US03-03 | Submit an evaluation that has already been submitted | Request is rejected with 409. Existing submission records remain unchanged. | Passed |
| TC-US03-04 | Submit an evaluation after its deadline | Request is rejected with 400 (`DEADLINE_EXPIRED`). No submission records are created. | Passed |
| TC-US03-05 | Submit a nonexistent evaluation | Request is rejected with 404 (`EVALUATION_NOT_FOUND`). No submission records are created. | Passed |
| TC-US03-06 | Submit a closed evaluation | Request is rejected with 400. No submission records are created. | Passed |
| TC-US03-07 | Submit an evaluation when the deadline is earlier than the current time | Request is rejected with 400 (`DEADLINE_EXPIRED`). | Passed |
| TC-US03-08 | Submit an evaluation when the deadline equals the current time | Submission is successful (201). | Passed |
| TC-US03-09 | Submit an evaluation when the deadline is later than the current time | Submission is successful (201). | Passed |

### Test Execution

Command:

```bash
python -m pytest tests/test_submission_workflow.py -v


## US04 – Lecturer Feedback

| Test Case ID | Test Scenario | Expected Result | Status |
|---|---|---|---|
| TC-US04-01 | Assigned lecturer views course feedback | HTTP 200; feedback content is displayed | Passed |
| TC-US04-02 | Lecturer not assigned to the course views feedback | HTTP 403 with the required permission message | Passed |
| TC-US04-03 | Student attempts to access lecturer feedback | HTTP 403 Forbidden | Passed |
| TC-US04-04 | Unauthenticated user attempts to access feedback | HTTP 401 Unauthorized | Passed |
| TC-US04-05 | Draft responses are excluded from feedback | Only submitted responses are displayed | Passed |
| TC-US04-06 | Lecturer views submitted ratings and comments | Submitted ratings and written comments are displayed correctly | Passed |
| TC-US04-07 | Completed evaluation count is calculated | Only submitted responses are counted | Passed |

### Test Execution

```bash
python -m pytest tests/test_lecturer_feedback.py -v
```

**Result:** 8 tests passed.
