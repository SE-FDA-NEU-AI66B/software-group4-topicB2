# Admin-managed account lifecycle — #254

Parent story: US12 #192; authentication/session requirements US01 #14 and US11
#183, BR4. Branch: `feature/admin-account-lifecycle`. No public registration,
production migration, production data edits, email delivery, merge or deploy is
performed by this change.

## Architecture and workflow

The existing Flask/Werkzeug authentication and SQLite/PostgreSQL boundary are
retained. Existing `users` records, password hashes, responses and answers are not
rewritten by migration. Optional additive tables hold lifecycle state, hashed
setup tokens and consumed CSV confirmation nonces. Without the reviewed migration,
existing P0 features continue; new provisioning APIs return an actionable 503.
No startup/build/deploy path executes the migration.

1. Admin opens `/admin/accounts`, enters name, email and Student/Lecturer role.
2. Server validates, detects existing email case-insensitively and atomically
   creates an invited account with an unusable password marker and a setup token.
   No shared/default password is assigned. Administrator provisioning is rejected.
3. The Admin sees a setup link once, with expiry and **private handoff required;
   no email sent** feedback. Deliver it only to the verified recipient through a
   private channel. No email transport is configured or claimed.
4. User opens `/activate#token=...`; the browser removes the fragment from history
   and keeps the token only in memory. The page explains that this sets a password
   for an existing account, rather than registering a new account.
5. User chooses and confirms a 12–128-character password. Server atomically checks
   token validity, expiry and account state, stores a Werkzeug password hash,
   consumes all outstanding tokens and increments the session version. User then
   signs in normally; password setup does not silently authenticate the browser.
6. Admin can search/filter active, invited and disabled users and reissue a setup
   link or initiate a password reset. A replacement invalidates earlier links.

Invitation TTL is 24 hours; reset TTL is one hour. Tokens use 32 cryptographically
random bytes; only SHA-256 digests are persisted. Raw tokens are returned only to
an authorized Admin at issuance and sent in the password-setup JSON body. They
are never placed in a query string, database, application log or localStorage.
The setup page loads only local assets, uses a restrictive CSP/no-referrer policy,
and account/token responses are `no-store`. Production requires existing HTTPS
and secure-cookie configuration. Treat the one-time handoff links as credentials;
do not include them in screenshots, tickets or logs. Lost links must be reissued.

## States, sessions and administrator protection

An existing account without a lifecycle row is `active`, session version zero.
An invited user cannot sign in until setup is completed. A disabled user cannot
sign in or access protected endpoints, including legacy endpoints with their own
role checks. Existing sessions are denied on their next request. Reactivation
increments the version, so old cookies remain invalid. Disabled invited accounts
resume as invited and require a fresh setup link. Public assets and health checks
remain public; logout remains safe to repeat.

Only administrators may mutate accounts. State/token/role operations coordinate
through the same PostgreSQL transaction advisory lock or SQLite `BEGIN IMMEDIATE`.
The actor is checked again under the lifecycle lock. Disable, role demotion and
reset issuance cannot modify the last active administrator, even if additional
administrator rows exist but are disabled. Concurrent disable attempts cannot
remove the final active administrator. Existing Student/Lecturer course-role
restrictions remain intact. No account deletion endpoint is introduced.

The old role-management page remains available for authorized role changes;
provisioning itself creates only Students and Lecturers. Password reset consumes
all old setup/reset tokens and revokes prior sessions. It does not reactivate a
disabled account. Sole-administrator recovery needs an independently reviewed
operator procedure; there is no public recovery or privilege-escalation bypass.

## CSV preview and confirmation

Header: `name,email,role` (UTF-8 BOM accepted). Maximum 64 KB and 200 rows. Names
are required, printable and at most 120 characters; email is normalized/validated;
roles must be `student` or `lecturer`. The preview reports row-level invalid input,
existing accounts, malformed columns and case-insensitive in-file duplicates.
Preview does not create accounts or invitation tokens.

A fully valid preview returns a signed confirmation containing the Admin identity,
canonical-row digest and random nonce, valid for 15 minutes. Confirmation requires
the same Admin session identity and the same CSV; server revalidates all rows
against current data under the transaction lock. Nonces are consumed once.
Account creation, invitation tokens and the consumed nonce commit together;
a later-row database failure rolls back the entire batch. Changed/stale previews
must be repeated. The UI invalidates confirmation when CSV/file input changes.
Batch invitation links are shown once for private delivery, never exported or
logged automatically.

## Course access changes

Existing add-enrollment/lecturer-assignment APIs remain available. The new
membership operation removes a relationship or adds the same-role target and
removes the source atomically. Disabled targets and mismatched roles are rejected.
Removing the last lecturer from a course with open/draft evaluations is refused;
transfer it to another enabled Lecturer instead.

Transfers never move student answers or response ownership. Removing a student
from a course removes future course access while preserving their submitted
feedback. Existing statistics count historical responses against current
enrollment, so response totals can exceed a subsequently reduced enrollment;
this release does not rewrite history to conceal that distinction.

## API map

| Route | Access / behavior |
| --- | --- |
| GET `/admin/accounts` | Admin provisioning UI |
| GET/POST `/api/admin/accounts` | Admin directory / create invited Student or Lecturer |
| PATCH `/api/admin/accounts/:id/state` | Admin disable/reactivate; last-active-admin guard |
| POST `/api/admin/accounts/:id/invitation` | Admin issue/reissue invitation or reset based on state |
| POST `/api/admin/accounts/import-preview` | Admin bounded CSV validation; no writes |
| POST `/api/admin/accounts/import-confirm` | Admin signed, expiring, actor-bound atomic batch |
| POST `/api/admin/memberships` | Admin remove/transfer membership |
| GET `/activate` | Public password setup page; no account creation |
| POST `/api/auth/set-password` | Valid unexpired one-time token required |

## Explicit migration and release plan

`tools/migrate_accounts.py --apply` creates `account_access`, `account_tokens`,
`account_imports` and `account_schema` transactionally. It is idempotent and verifies
expected columns. Existing schema version 1/checksum is retained; base PostgreSQL
verification now recognizes the known supplemental tables. No production URL is
embedded in code or passed through logs.

Only after independent review and explicit operator authorization:

1. Take a private backup/snapshot of the chosen database. Test restore on a
   disposable copy, and verify all current users/responses/answers counts.
2. Rehearse the migration and test provisioning on an isolated SQLite database or
   PostgreSQL branch, using the same reviewed code.
3. Configure `EDUSURVEY_MIGRATION_DATABASE` securely to the reviewed SQLite path
   or direct PostgreSQL URL and explicitly run:

   ```sh
   python tools/migrate_accounts.py --apply
   ```

4. Verify original data counts, lifecycle schema, authentication and all P0 flows.
   No existing users should have been changed or tokens issued by migration.
5. Release only the reviewed code through green CI and the existing deployment
   process. Begin lifecycle operations after old instances have drained.

Migration DDL failure rolls back atomically. Before lifecycle use, the additive
schema may remain alongside older code without rewriting data. **After accounts
are disabled or sessions revoked, do not roll back to code that ignores lifecycle
state:** it would ignore those restrictions. Keep the schema/data and use a
reviewed fix-forward or maintenance-mode release that preserves enforcement.
Never drop the tables or restore an old snapshot merely to roll back application
UI changes. No rollback/drop command is run automatically.

## Verification

Full local regression: **404 passed, 0 skipped** across SQLite, isolated PostgreSQL
and Chromium; Ruff and diff checks pass. Existing tests/assertions are preserved.

New tests cover migration preservation/idempotence, single-use/expired/replaced
tokens, disabled login and replayed cookies, reset session revocation, unauthorized
roles and cross-origin requests, last-active-admin races, CSV expiry/actor binding/
duplicates/changed input/replay/transaction rollback, and membership preservation.
PostgreSQL tests also use concurrent token redemption and duplicate creation;
only one attempt succeeds. Mobile Chromium exercises actual Admin creation,
password setup, sign-in, directory search and disabling the resulting session.
All database tests use disposable local schemas/files, never production.

Desktop/mobile screenshots contain only synthetic data and no setup credentials:
[Admin desktop](evidence/accounts-254/admin-desktop.png),
[Admin phone](evidence/accounts-254/admin-phone.png),
[CSV desktop](evidence/accounts-254/csv-preview-desktop.png),
[CSV phone](evidence/accounts-254/csv-preview-phone.png).

Remaining integration: automated email delivery is not configured; invitations
use explicit private handoff. No public Sign Up or public password-reset request
is added. Audit-log retention, email delivery/recipient verification and production
migration/deployment rehearsal remain operator/integration follow-ups.
