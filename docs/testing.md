# Testing Documentation

## US11 – User Sign Out

Related Issue: #169

### Test Cases

| Test Case ID | Test Scenario | Expected Result |
|---|---|---|
| TC-US11-01 | Login with valid credentials | HTTP 200 and authenticated is true |
| TC-US11-02 | Login with incorrect password | HTTP 401 Unauthorized |
| TC-US11-03 | Access current user without login | HTTP 401 Unauthorized |
| TC-US11-04 | Access current user after successful login | HTTP 200 and user information is returned |
| TC-US11-05 | Sign out successfully | HTTP 200 and authenticated is false |
| TC-US11-06 | Verify session is cleared after logout | user_id and role are removed from session |
| TC-US11-07 | Access protected resource after logout | HTTP 401 Unauthorized |
| TC-US11-08 | Sign out without authentication | HTTP 200 and authenticated is false |
| TC-US11-09 | Insert duplicate user email | SQLite IntegrityError is raised |

### Test Execution

Run authentication tests:

```bash
python -m pytest tests/test_auth.py -v
```

Run all tests:

```bash
python -m pytest -v
```

### Test Environment

- pytest
- Flask test client
- Temporary SQLite database
- No production database required
- No running application server required
