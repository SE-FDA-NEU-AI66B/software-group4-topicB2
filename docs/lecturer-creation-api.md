# US13 shared evaluation creation API (#198)

P1 parent #193; reuses #40 and coordinates US08 #38, frontend #197 and queries/
transactions #199. No duplicate POST endpoint, schema migration or administrator/
lecturer creation UI is introduced. Existing P0 workflows remain unchanged.

## Contract

`POST /api/evaluations` accepts the existing course_id, title, deadline and ordered
questions fields. A Lecturer must currently be assigned to the selected course;
Administrator creation follows US08 without requiring a lecturer assignment.
Student/anonymous/deleted actors cannot create. Identity/created_by comes only
from the signed session and the current database account, never body/query IDs
or role claims. Role, course and assignment are checked under BEGIN IMMEDIATE in
the same transaction as evaluation/question storage.

| Field | Validation / stored behavior |
|---|---|
| course_id | Positive integer, not bool; course must exist |
| title | Nonempty string after trim; trimmed value stored |
| deadline | Required ISO-8601 datetime; explicit offset preserved, naive values retain existing local/naive convention |
| questions | Nonempty list; 0 rejects, 1/5/6 succeed; five is not a maximum |
| question_text | Nonempty trimmed string |
| question_type | rating or text |
| is_required | Boolean, defaults true |

Success remains 201 with message, evaluation_id, course_id, title, deadline,
status=draft and questions_created. **Added** `questions` is the persisted ordered
list of `{id,question_text,question_type,is_required,question_order}`; this allows
#197 to display exactly the saved configuration/IDs on confirmation. Existing
response fields and the draft lifecycle are preserved. Creation does not publish
a draft to students; student opening/submission rules are not relaxed. The
current API parses the deadline but does not add a new future-only creation rule;
the separate deadline-update contract remains unchanged.

Unassigned Lecturer: 403 / COURSE_ACCESS_DENIED with exactly:

> You do not have permission to create an evaluation for this course.

Missing deadline retains 400 / MISSING_DEADLINE and now uses US08's exact
`A deadline is required.`. Other validation codes/statuses are retained. Valid
body with anonymous/deleted actor gives 401; Student gives 403; nonexistent course
gives 404. The existing validation-first ordering is retained: malformed/missing
data can return 400 before authentication, always without writes. Authorization
still precedes any persistence. Unknown actor/creator fields do not override the
session. SQLite write failure returns the existing safe 503 DATABASE_UNAVAILABLE.

All inserts, the role/assignment check and the persisted-question read-back use
one transaction. A second-question failure rolls back both the evaluation and
earlier questions; a retry succeeds after removing the test-only injection.
Schema/relationships/parameter binding are reused for #199 review, with no new
tables. #197 still owns actual form/confirmation rendering; returning five JSON
items does not claim a complete frontend or a reload configuration-read endpoint.

## Functional checks

```bash
python -m pytest -v tests/test_evaluation_creation.py tests/test_smoke.py
python -m ruff check . --output-format concise
git diff --check
```

Windows / Python 3.12.6 / pytest 9.0.2: **55 passed in 8.90s** in the focused run.
Twenty new variants plus retained smoke tests cover 0/1/5/6 question counts,
ordered persisted/display-response values, actor/creator/course association,
anonymous/Student/deleted actors with spoofed IDs, ownership of course 1 not
authorizing course 2, US08 admin creation, missing/invalid data and no writes.
The injected SQLite ABORT fires only after the evaluation and first question
exist, records that it was reached, and verifies exact rollback and successful
retry. Temporary SQLite and the existing fixed clock are used; no real data is
initialized or modified.

Full suite with installed Chrome selected via PLAYWRIGHT_CHROMIUM_EXECUTABLE:
`python -m pytest -q --junitxml=junit.xml` -> **277 passed in 154.68s**, zero
failures/errors/skips (257 retained + 20 new). The selected-course ownership case
was strengthened and the focused run passed again; no product code changed after
the full run. Repository-wide Ruff and diff checks pass.

## Actual creation latency

```bash
python -m tools.measure_creation_latency --samples 30 --warmups 3
```

This executes real loopback HTTP POSTs against threaded Werkzeug/Flask and a
temporary SQLite database. It reuses the existing P0 seed profile (22 synthetic
users, one course, three starting evaluations, 20 submitted responses), one
preauthenticated assigned lecturer, five questions per request and concurrency 1.
Three warmups are discarded; 30 sequential warmed samples are recorded. The
final capture ran after pytest finished; other background OS load is uncontrolled.

Monotonic interval: immediately before HTTP POST until the 201 JSON body is fully
consumed, after commit. Database seeding, cookie/payload preparation and separate
post-request SQL verification are excluded. TLS, production proxy, login and
browser rendering/navigation are absent. Every sample verifies 201 plus five
response items, and committed course/creator/question counts are checked outside
the timer. Connection/config/clock state is restored and temporary storage removed.

[Raw timing/profile/source hashes](evidence/198/creation-latency.json), captured
2026-11-16 Asia/Saigon: **p50 17.488ms, p95 20.084ms, maximum 20.853ms**; all 30
samples satisfy the <=3000ms reference comparison on this local backend profile.
p50 is median and p95 is nearest-rank ceil(.95*N). This is real creation latency,
not total pytest runtime, but it does **not** certify the US13 deployed visible
confirmation requirement. #197 and an actual release/network/load profile still
need browser action-to-visible-outcome evidence. Do not present these numbers as
public production latency or a synthetic 2999/3000/3001ms boundary test.

The initial capture could not clean up the legacy seed helper's open SQLite
connection on Windows. The measurement wrapper now explicitly closes seed
handles, and the final full capture completed with cleanup; no failed capture is
reported as a successful measurement.

Independent frontend/query review remains pending. No automatic merge,
production migration, deployment or actual lecturer UI certification is claimed.
