# US12 administrator API (#195)

P1 backend scope, parent #192; coordinate frontend #194 and database #196.
No Sprint 4 assignment or existing administrator HTML interface is claimed.
Implemented contract below is for frontend integration after independent review.

## Settings scope decision

No prior setting catalog or PO decision was found in #192/#195/#196 or their
comments. The requester delegated the minimal implementation choice on 2026-11-16
after being offered the support_contact proposal. This branch selects that one
key. **Formal PO and #196 database-owner agreement remain review gates**; no PO
approval or teammate review is fabricated. Confirm this definition before merging
or integrating #194. Additional settings require their own defined consumers and
review, not arbitrary key/value writes.

| Key | Type/validation | Default | Affected function |
|---|---|---|---|
| `support_contact` | String, trimmed length 1-200 Unicode characters; no interior C0/DEL control characters | `Contact your university administrator if you need access.` | Public `/` and `/login` render the saved guidance on the next request; Jinja escapes HTML |

The setting is public contact guidance, never a password, token or private data.
It does not change role rules, rating/text limits, Due soon/expiry, enrollment or
submission rules. Home/login responses are no-store so stale guidance is not
intentionally cached. An old/unmigrated DB uses the default on reads; updates
return 503 with an operator action until migration. A DB outage also leaves
public sign-in guidance available with the default; existing `/health` still
checks the DB independently and can report 503.

## Authentication and permissions

All management routes authenticate from the signed session's user_id and reload
the account's current role from SQLite. Body/query IDs and roles cannot choose
the actor. Every protected route using login_required now refreshes the role;
existing submission/evaluation creation routes already query the authenticated
account directly. Deletion/unsupported role clears the session. APIs retain JSON
401; anonymous HTML retains the approved login redirect behavior. This does not
implement copied-cookie revocation (#216).

Student/Lecturer denial is 403 / FORBIDDEN with exactly:

> You do not have permission to access this area.

Role/setting writes also recheck the actor under BEGIN IMMEDIATE in the same
transaction as the update. Existing sessions pick up promotion/demotion on their
next protected request, including the caller's self-demotion. A role change does
not delete course assignments, enrollments or submitted responses. Memberships
alone never override the current role. Self-demotion is allowed; there is no
invented last-administrator or account-creation policy. PO should review that
operational risk before enabling this interface.

## Routes and status contracts

| Method / route | Success | Invalid/error behavior |
|---|---|---|
| GET `/api/admin` | 200 links to implemented users/settings APIs | 401 anonymous/deleted actor; 403 non-admin |
| GET `/api/admin/users` | 200 `{users:[{id,email,full_name,role}]}` ordered by id | No password hashes; currently unpaginated, intended for this small demo scope |
| PATCH `/api/admin/users/<int:user_id>/role` | 200 `{user:{id,role}}` | Body exactly `{role:<domain value>}`; 400 INVALID_REQUEST/INVALID_ROLE; 404 USER_NOT_FOUND |
| GET `/api/admin/settings` | 200 catalog with key/value/type/min_length/max_length/updated_at | Unset/unmigrated value uses documented default, updated_at=null |
| PUT `/api/admin/settings/support_contact` | 200 `{setting:{key,value,updated_at}}` | Body exactly `{value:<string>}`; 400 INVALID_REQUEST/INVALID_SETTING_VALUE; unknown key 400 UNSUPPORTED_SETTING; missing migration 503 SETTINGS_NOT_INITIALIZED |
| Existing PUT `/api/evaluations/<id>/deadline` | Existing future-deadline update reused | Same admin gate/exact 403; existing validation/status/rule behavior retained |

Domain values are exactly `student`, `lecturer`, `administrator` (case-sensitive).
Objects/booleans/null/arrays, unknown fields and SQL-like role strings are rejected
without writes. No user create/delete or competing deadline endpoint is added.
SQLite failures retain the existing sanitized 503 DATABASE_UNAVAILABLE contract.
Settings timestamps are ISO-8601 UTC, including +00:00; actor ID is persisted only
from the authenticated session. Management responses with a session are no-store.

Examples (after authenticated administrator login):

```json
{"role":"lecturer"}
```

Send that body via PATCH to `/api/admin/users/1/role` (1 is an example target,
not the actor). To change public contact guidance:

```json
{"value":"Contact the training department during office hours."}
```

Send via PUT to `/api/admin/settings/support_contact`; GET the catalog and reload
the login page to observe the persisted text. Existing default admin landing stays
`/account`; #194 supplies real management screens/navigation later.

## Persistence and non-destructive setup

`users.role` and its existing three-role CHECK are reused. Fresh schema gains only
`system_settings(key,value,updated_by,updated_at)`, with a key/length constraint and
nullable FK to users. Role/setting SQL uses bound parameters and transaction
contexts. The new table is empty initially; the default is an application fallback,
not a guessed seed setting. No audit/history of previous role values is claimed.

For an existing deployment, back up via the existing SQLite backup procedure,
review the target database path, then run from the repository root:

```bash
python -m tools.migrate_us12_settings /absolute/persistent/edusurvey.db
```

The migration opens only an existing file (`mode=rw`), validates the users table,
creates the settings table transactionally if missing, and verifies its columns.
It does not invoke schema.sql/reset/seeding, change existing users/evaluations,
or overwrite settings on a repeated run. Incompatible schema fails for operator
review. A missing DB is not created. This migration was executed **only on
temporary test databases**; applying it to an actual deployment remains an
operator step after backup/review. A code rollback can leave the additive table
in place; do not reset/drop user data to roll back the app.

## Verification and review

```bash
python -m pytest -q tests/test_admin_api.py tests/test_auth.py tests/test_smoke.py
python -m ruff check src/admin.py tools/migrate_us12_settings.py tests/test_admin_api.py
```

Local Windows / Python 3.12.6 / pytest 9.0.2: **112 passed in 25.33s**. This includes
50 US12 variants plus retained authentication/smoke coverage. All data is temporary
SQLite; application configuration, time, connection patches and sessions are
isolated/restored. Tests cover denied Student/Lecturer/anonymous operations,
forged/stale roles and query impersonation, all three assigned roles, old-client
permissions, self-demotion, transaction-time recheck, invalid/no-write cases,
exact 1/200/201 setting lengths, persisted UTC/actor, escaped login guidance,
failed-write preservation and repeatable migration without data loss.

The initial focused run had 2 failed / 106 passed due to naive timestamp test
expectations; the API emits UTC. Tests were corrected to assert the documented
offset, with no production time behavior weakened and no failing test skipped.
Existing home smoke now uses the isolated API fixture because login renders a
database-backed setting. Formal PO/#196 and independent review remain pending;
no administrator frontend or production migration is claimed by these results.

Final full suite (installed Chrome selected through
PLAYWRIGHT_CHROMIUM_EXECUTABLE): `python -m pytest -q --junitxml=junit.xml` ->
**279 passed in 163.46s**, zero failures/errors/skips (229 retained + 50 US12).
[Per-module evidence](evidence/195/local-tests.json). No production migration or
administrator UI verification is implied by this local backend result.
