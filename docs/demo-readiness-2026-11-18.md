# Demo readiness — 18 November 2026

Issue: #248. Backend/UI behavior and remaining scope: [workspace notes](demo-workspace.md).

## Safe synthetic dataset

`tools/enrich_demo.py` adds 24 reserved `DEMO-*` courses, 6 lecturers, 30 students,
1 administrator, 24 evaluations with 120 ordered questions and 264 completed
responses (1320 answers). Each course receives 11 synthetic responses across
course content, teaching delivery, workload and assessment. Student 1 is enrolled
in all demo courses and has no submitted responses, allowing a live submission.
Three evaluations are closed; the others have future deadlines relative to the
seed time. Existing P0 demo accounts and courses are untouched.

Set `EDUSURVEY_DEMO_PASSWORD` to a chosen credential of at least 12 characters;
set `EDUSURVEY_DEMO_DATABASE` to an **isolated demo** database. Run:

```sh
python tools/enrich_demo.py
```

For a new local database, first set `EDUSURVEY_DATABASE` to an unused SQLite path
and run `python -m src.init_db --m5-demo`, then point `EDUSURVEY_DEMO_DATABASE`
at that path. For PostgreSQL use the existing reviewed migration on a dedicated
demo/test database first. Never run the destructive SQLite schema against an
existing database. The seed CLI refuses the production runtime environment.

Synthetic emails:

- `student1@demo.edusurvey.invalid` through `student30@demo.edusurvey.invalid`
- `lecturer1@demo.edusurvey.invalid` through `lecturer6@demo.edusurvey.invalid`
- `admin@demo.edusurvey.invalid`

The script never prints the credential or database URL. It inserts transactionally,
locks concurrent seed attempts, skips existing reserved course codes, reuses
matching-role accounts and never updates existing records. Repeating the seed
returns zero additions. To reset the demonstration, recreate only the isolated
demo database; do not delete production rows. No production seed was performed.
No migration is needed for this release; rollback application code remains schema
compatible. Review and merge the management PR before the stacked seed PR.

## Acceptance evidence

- Full local regression: 372 passed, 0 skipped, including PostgreSQL UTF-8 and
  Chrome laptop/phone tests, before the additional dedicated PostgreSQL seed case.
- Ruff passed; no existing test removed, skipped or assertion weakened.
- New cases exercise draft persistence, invalid input, role revocation, course
  ownership, exactly five questions, status changes, duplicate membership,
  last-admin guard and additive seed idempotence/preservation.
- Six workspace screenshots inspected from isolated synthetic data; no JavaScript
  errors or horizontal overflow at 1440px and 390px.
- Public `/health` returned `200`, `database=ok`, `status=ok`. This endpoint does
  not expose a commit SHA. New changes have not been deployed.
- CI results and final PR SHAs are recorded in the GitHub PRs. Local checks do
  not substitute for Actions or independent approval.

## 12-minute demonstration for 19 November 2026

| Minute | Demonstration |
| --- | --- |
| 0–1 | Explain Student/Lecturer/Admin roles and the five P0 stories; show public URL and health. |
| 1–3 | Student login, dashboard, course search, existing evaluation list filters and deadlines/status. |
| 3–5 | Open an evaluation, show required-field validation, save partial draft, reload, complete and submit. |
| 5–6 | Show Completed status, duplicate prevention and logout; protected page redirects to login. |
| 6–8 | Lecturer login, assigned courses, response count, ratings, grouped comments and statistics. |
| 8–10 | Create a new evaluation with five questions for an assigned course, save draft, review questions and open it. |
| 10–11 | Admin directory, add a course, assign lecturer/enroll student; explain last-admin and course-role guards. |
| 11–12 | Show persistence after reload, CI evidence, scope still pending and production deployment status. |

Use the enriched isolated demo only after rehearsal. Production can demonstrate
only features from its deployed approved SHA; do not claim the pending PR features
are already live. Render Free cold starts must be measured/reported separately
from normal warm interaction latency. Keep a pre-opened healthy session and a
local isolated demo as the fallback; do not claim the local URL is production.

## Still pending

Full user provisioning/deletion, removal/reassignment of memberships, settings
management, outbound scheduled reminders, question editing after creation,
exports and advanced comparison charts. Lecturer deadline editing remains
administrator-only through the existing endpoint. Deployed BR8 <=3-second
acceptance measurements remain pending after approval/deployment.
