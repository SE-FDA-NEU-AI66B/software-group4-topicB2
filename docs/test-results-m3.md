# Milestone 3 — P0 Workflow Test Results

## Test Execution

- **Test framework:** pytest
- **Command:** `python -m pytest -v`
- **Result:** 9 tests passed
- **Status:** Passed for the implemented and tested routes

## Automated Test Coverage

| Test | Expected result |
|---|---|
| Home route | HTTP 200 |
| Evaluations route | HTTP 200 |
| Submission without login | HTTP 401 — `UNAUTHORIZED` |
| Submission with missing answers | HTTP 400 — `MISSING_REQUIRED_ANSWERS` |
| Submission after deadline | HTTP 400 — `DEADLINE_EXPIRED` |
| Duplicate submission | HTTP 409 — `DUPLICATE_SUBMISSION` |
| Submission for nonexistent evaluation | HTTP 404 — `EVALUATION_NOT_FOUND` |
| Submission to closed evaluation | HTTP 400 — `EVALUATION_CLOSED` |
| Unauthorized response guidance | Error code, message, and action are present |

## Known Limitations

The current application does not yet implement login/logout routes or lecturer feedback access. The submission endpoint validates requests but does not persist successful submissions or answers to the database.

These workflows therefore remain unverified and require implementation and further end-to-end testing before all P0 acceptance criteria can be considered complete.

## Conclusion

All 9 automated tests passed for the currently implemented routes and business-rule validations. This confirms the tested behavior only; it does not establish that all P0 workflows are complete.
