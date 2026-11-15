# P0 release verification and M4 rehearsal (#210)

Parent #200; dependencies #201/#202/#205/#206/#209 and approved P0 contracts
#188 / #217. Verification date: 2026-11-15. **Local rehearsal is recorded; public
release acceptance remains pending.** The issue/PR closing link is not evidence
that a service, phone check or rollback has been verified.

## Candidate and evidence provenance

| Field | Actual evidence / status |
|---|---|
| Current code candidate | Main `6acf0dd42b0a8b56831deedc519c194b474a519c` (#226 merged) |
| Latest observed candidate CI | [Successful CI run](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43731613604); metadata in [main-ci.json](evidence/210/main-ci.json) |
| Public HTTPS origin / deployed SHA / v1.0 | Not supplied or discovered; no repository homepage, GitHub deployment or release at inspection. External hosting is not ruled out by empty GitHub metadata |
| Test environment | Local Windows / Python 3.12.6 / pytest 9.0.2; fresh headless Chrome contexts at laptop/phone viewports |
| Real private desktop + physical phone + no VPN | Pending on actual public release; a viewport emulator is not a physical phone |
| Platform logs/live health/rollback | Pending #205/#206/#209 service access and real deploy IDs |
| Independent teammate recorded review | Pending; no self-approval or automatic merge |

[Release discovery metadata](evidence/210/release-discovery.json) records the
actual repository homepage/deployment/release lookup and its UTC timestamp.

The first pinned baseline `ebb938d` produced **5 failed / 185 passed in 152.65s**
(190 collected; no skips). Its stale FK/error-handling and Windows-specific test
expectations were already corrected by #226, which merged while this audit was
running. [Historical local report](evidence/210/main-ebb938d-local.json) and
[historical mutation](evidence/210/mutation-ebb938d.json) are retained. This task
does not alter existing tests or production code to turn that baseline green.
Current evidence below supersedes it only for the newer pinned candidate.

## Reuse existing P0 tests when explaining M4

Open [testing.md](testing.md) for exact case IDs/results. These are existing
nodes, not new duplicate credential tests or invented coverage.

| Story | Normal / error example to explain | Applicable boundaries and real node |
|---|---|---|
| US01 #14 | `tests/test_auth.py::test_login_success`; existing `test_login_wrong_password` / `test_login_unknown_email` retain generic canonical error and privacy | No numeric credential limit is inferred. Use the existing empty/missing input and role/session cases, not an invented boundary |
| US02 #18 | `tests/test_student_evaluations.py::test_student_evaluations_success`; `test_student_evaluations_requires_login` | `test_student_evaluations_due_soon_24_hour_boundary`: 86399/86400/86401 seconds -> Due soon/Active/Active. `test_student_evaluations_deadline_boundary` tests expiry before/at/after |
| US03 #22 | `tests/test_submission_workflow.py::test_submission_success_persists_response_and_answers`; `test_duplicate_submission_does_not_modify_existing_records` and canonical-message nodes | #184 rating 0/1/2/4/5/6; trimmed text 1999/2000/2001; required answers 4/5; `test_submission_deadline_boundary` rejects deadline equality |
| US04 #50 | `tests/test_lecturer_feedback.py::test_feedback_displays_submitted_ratings_and_comments`; `test_lecturer_cannot_view_unassigned_evaluation` | #185 `test_feedback_completed_count[count-19/count-20/count-21]`: all 200, exact N; 20 is an acceptance example, not a maximum; drafts excluded |
| US11 #183 | `tests/test_auth.py::test_logout_success`; `test_student_page_denied_after_logout` / `test_lecturer_feedback_denied_after_logout` | #186 `test_anonymous_logout_is_idempotent`; repeated current-client logout and HTML/API access contracts are checked. Copied-cookie revocation remains #216, not a pass |

Real browser implementations are reused from `tests/test_p0_browser_contracts.py`:

- `test_logout_navigates_to_login[laptop]` and `[phone]`: actual login/list/answer/
  review/submit, SQLite write, receipt reload, Completed list and logout/API denial.
- `test_lecturer_feedback_click_through[laptop]` and `[phone]`: lecturer login,
  assigned feedback counts/ratings/comments, reload, navigation and logout.
- `test_submission_deadline_race_and_retryable_logout`: server-side deadline
  rejection after opening; real SQLite state stays unchanged and logout retry works.
- `test_open_evaluation_error_explains_next_action[closed/unenrolled]`: server
  rejects stale availability, visible error and Back to evaluations recovery.

Those local cases use synthetic accounts (`student@test.com`, `lecturer@test.com`)
and disposable data with controlled time. They do not use or verify production
demo credentials. A normal local UI flow does not establish public HTTPS access.

P0C-01/02/05/06/08 are implemented by #223; use the current update at the end of
[p0-acceptance-review.md](p0-acceptance-review.md), not its historical pending rows.
P0C-09 copied-cookie policy and P0C-10 through P0C-18 timing work remain separate.
No 2999/3000/3001ms budget-classifier test or real deployed latency node is claimed
implemented by this evidence task. The approved visible-outcome criterion is
inclusive <=3000ms including navigation; suite runtime and Flask timings are not
substitutes for that measurement.

## Actual controlled red/green rehearsal

```bash
python -m pip install -r requirements-dev.txt
python tools/rehearse_business_rule.py --revision 6acf0dd
python -m ruff check tools/rehearse_business_rule.py
git diff --check
```

The runner exports only pinned `src`/`tests` into a temporary directory, runs the
existing three-case US02 boundary node, changes exactly one expression there,
restores the copied bytes in `finally`, and reruns the identical node. It verifies
the workspace source hash is unchanged and removes the temporary directory. It
does not mutate/deploy the working app or write a production database.

| Stage | Actual result |
|---|---|
| Original strict `deadline < now+24h` | 3 passed; process exit 0 |
| Temporary `deadline <= now+24h` | 1 failed / 2 passed; process exit 1; only `TC-09-at` fails because 24h becomes Due soon instead of Active |
| Restore original source bytes | 3 passed; process exit 0; restored source hash equals original |

[Mutation evidence](evidence/210/mutation.json) contains sanitized real pytest
output, counts, source hashes, pinned SHA, environment and measured stage durations.
It demonstrates detection of this controlled defect, not a newly discovered
production bug or comprehensive mutation coverage. Preserve dated evidence when
repeating: use `--output <new-report-path>` rather than relabeling a new run as the
original. Do not commit or deploy the deliberately incorrect expression.

## Public release walkthrough - not yet executed

Before starting, record actual HTTPS origin, provider-deployed SHA, CI run,
UTC/local time, browser versions, real phone model, network/VPN state and load.
Use a fresh private desktop context and the actual phone browser. Record account
roles/approved synthetic demo identities, never passwords/tokens/cookies in images.
The seeded account needs a fresh allowed submission slot; do not reset a live DB
or infer that local fixture identities exist on the release.

| Step | Required actions / observation | Public result |
|---|---|---|
| Health before | Anonymous HTTPS `/health` -> 200 with expected sanitized JSON; record deployed SHA and no-store | NOT RUN |
| US01 | From first public page, sign in using approved seeded student; usable role landing | NOT RUN |
| US02 | Open assigned list through visible navigation; explain states and availability | NOT RUN |
| US03 | Open an available survey, required-answer validation, review, submit once; record sanitized receipt ID, reload and confirm persisted completion | NOT RUN |
| Server rejection | Use an operator-prepared synthetic rejection case or normal duplicate attempt; capture actual server status, visible what/why/next-action and unchanged data. Do not mock the network or damage production for evidence | NOT RUN |
| US11 student | Visible Sign out -> login; old context's protected API 401 and browser HTML redirects as approved | NOT RUN |
| US04 | From first page sign in as approved lecturer; assigned-only feedback/count/ratings/comments; recover through visible links | NOT RUN |
| US11 lecturer | Visible Sign out -> login; subsequent protected access denied | NOT RUN |
| Phone | Repeat click-through in actual phone/private context, no install/VPN; capture safe viewport/error evidence | NOT RUN |
| Health/rollback after | Reuse #205 real rollback evidence: exact before/target/live deploy IDs, schema compatibility, retained data, health and P0 recheck. Do not claim a local backup/restore test is an application rollback | NOT RUN |

The page transitions must use visible controls after the initial URL. Direct
`/health` inspection is the separate health demo, not a shortcut replacing P0
navigation. A controlled local DB expiry test cannot stand in for a real released
server rejection. If the public rejection cannot be triggered safely using normal
UI/approved demo state, leave it pending and coordinate a seeded case with #204.

For each step store observed pass/fail, actual request/status, time, sanitized
image/receipt and defect issue if needed. Leave unknown fields empty/pending until
observed. Re-run after any candidate-SHA change rather than combining unrelated
deployments into one verification record.

## Completion gate

- [x] Existing P0 normal/error/applicable boundary nodes located without duplication
- [x] Pinned safe mutation produces real red result, then restored green
- [x] Historical failing baseline retained instead of hidden
- [ ] Actual public URL and provider-deployed SHA verified
- [ ] All five P0 flows, persistence and real rejection verified on private desktop and physical phone
- [ ] Public health and actual hosted rollback rechecked
- [ ] Deployed visible-outcome timing evidence completed under approved profile
- [ ] Independent teammate recorded review/approval

PR includes `Closes #210` as requested; keep it draft/unmerged until public
acceptance gates are satisfied so the closing link does not prematurely close
the task. No automatic merge, self-approval or fabricated release proof.

## Current candidate execution results

Windows / Python 3.12.6 / pytest 9.0.2, installed Chrome selected through
PLAYWRIGHT_CHROMIUM_EXECUTABLE:

```text
python -m pytest -q --junitxml=junit.xml
200 passed in 173.05s (0:02:53)
```

[Candidate local report](evidence/210/main-6acf0dd-local.json) contains real module
counts, zero failures/errors/skips and explicit unverified public fields. All
existing P0 browser cases and `/health` healthy/failed DB checks ran in that suite.
The backup round-trip test passed too; it is an isolated database recovery check,
not a hosted application rollback. No new pytest case or production change is
introduced by #210. Script Ruff and `git diff --check` passed. The actual main CI
link above is green for the same candidate; neither green result verifies a
running public release or physical device.
