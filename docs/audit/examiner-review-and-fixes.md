# Strict examiner review and verified fixes

Date: 2026-11-16, Asia/Ho_Chi_Minh. Baseline main:
`0f924cdddf27a0d76881e3350897db87f91028b6`, after independently merged PRs
#240/#241/#242. Baseline: **298 passed in 92.01s**, no skipped tests.
Final local suite: **318 passed in 124.76s**, zero failures/errors/skips.
**Overall M5 release readiness: BLOCKED**, despite local regression success.

The review uses the supplied M5 brief and repository requirements/design/UI/
testing/SETUP/README/operations/sprint records. It does not invent a marking
rubric, claim a numeric grade, certify human participation or require P1 features
as additional P0 stories. Main already contains the previous evaluation-count,
receipt/concurrency and keyword fixes; those were not reimplemented here.

## Findings and corrective evidence

Categories: **CONFIRMED BUG**, **SAFE UX FIX**, **ENHANCEMENT**, **NEEDS APPROVAL**.
Category describes the decision; Status below uses only PASS/FAIL/BLOCKED/
NOT VERIFIED. PASS means the scoped correction/check passed, not perfect product.

| Finding | Severity | Evidence | Root Cause | Fix | Regression Tests | Status |
|---|---|---|---|---|---|---|
| EX-A01 — CONFIRMED BUG: deleted account could still open protected pages/APIs with its signed session | High | Six reproduced failures before fix; only `/api/auth/me` previously checked whether the account still existed | Shared guard trusted presence of user_id; direct page/data requests skipped account existence | Verify account before granting access; clear deleted-account session, retain existing API 401/message and HTML login redirect | `test_auth.py::test_deleted_account_cannot_reuse_protected_session` (6 paths/roles); existing deleted-account `/me` assertion retained | PASS |
| EX-A02 — CONFIRMED BUG: downgraded lecturer session still read assigned feedback | High | Real credential login, DB role changed to student, feedback API still returned 200; one pre-fix failure | Restricted routes checked cached cookie role without checking current DB role | Current DB role must also belong to allowed roles; return existing FORBIDDEN 403 without feedback; no role auto-switch or new API codes | `test_backend_runtime.py::test_reassigned_role_cannot_keep_lecturer_feedback_access` checks six page/API/aggregate routes and payload absence | PASS |
| EX-UX01 — CONFIRMED BUG / SAFE UX FIX: HTML/malformed API replies exposed parser errors without useful recovery | Medium | Representative HTML-503 browser reproduction failed before fix; all six new combinations pass afterwards | `response.json()` failures escaped into raw UI messages; complete form also assumed an object root | Human-readable fallback only for unreadable replies; keep approved business errors and working labels; preserve retry/back/edit controls and do not fabricate submission success | `test_p0_browser_contracts.py::test_unreadable_api_response_has_useful_recovery` (list/questions/submit × HTML503/malformed200) | PASS |
| EX-T01 — CONFIRMED BUG in test quality: shared frozen clock changed absolute instant between timezones | Medium | UTC−5 and UTC+7 invariant tests failed; fixture attached tzinfo rather than converting the same instant | Aware test clock returned the same wall hour in every zone | Convert the fixture's explicit UTC instant to requested zone; naive fixture value/old expected results remain unchanged; production timezone policy untouched | `test_backend_runtime.py::test_frozen_fixture_clock_represents_one_instant` (2); 96 related cases and full suite passed | PASS |
| EX-D01 — SAFE UX FIX in documentation: current UI described US04/US11 as unimplemented | Low | Historical M3 prose contradicted merged pages and real browser tests | Old snapshot presented without current implementation qualification | Add dated current status/entry table; retain historical wireframes/screenshots and original snapshot context | Source/route inspection, existing click-through tests and local link checks | PASS |
| EX-D02 — SAFE documentation correction: SETUP suggested rerunning initialization to repair missing tables | Medium | Initializer deliberately refuses existing targets; instruction cannot repair existing data safely | Walking-skeleton repair text predated fail-closed startup | Describe path/mount inspection and isolated recovery; link disposable demo launcher; explain CI3.12/local3.14 instead of exclusive3.14 prerequisite | Existing no-overwrite/recovery/launcher tests retained; guidance/link review | PASS |
| EX-D03 — SAFE documentation clarification: old design table advertised historical endpoint names/logout errors | Low | Current API routes and approved logout idempotency differ from M2 proposal | Historical design not distinguished from current implemented contract | Add current canonical route/contract note; do not rename working APIs to fit old table | Existing API tests and route-map inspection; historical table retained | PASS |
| EX-P01 — NEEDS APPROVAL: timezone semantics for legacy offset-free deadlines | Medium | Offset-aware backend tests pass; naive timestamps have no explicit timezone in their representation | Default interpretation across server/browser zones is not a fully documented contract | No automatic UTC conversion/data migration/UI formatting change; PO decides legacy zone/new-input policy, then use explicit deterministic cross-zone acceptance cases | Existing aware-boundary tests remain; no invented naive-zone expected value | BLOCKED |
| EX-P02 — NEEDS APPROVAL: copied signed-cookie revocation / automatic role-switch lifecycle | Medium | Existing #216 contract discussion remains unresolved; current-session clearing and over-age rejection are different | Client-signed sessions do not provide per-cookie server-side revocation | No authentication rewrite or new schema. This fix denies deleted/downgraded account data but does not claim general replay revocation | Real logout/back/age tests below; saved-cookie revocation not claimed | BLOCKED |
| EX-E01 — ENHANCEMENT: full administrator/creation/reporting UI and broader accessibility certification | Optional/P1 | US12/US13 work remains in separate PRs; P0 admin role has account/sign-out landing | Outside five-P0 mandatory delivery and current safe-fix scope | Do not add features/redesign or invent a failure against the instructor brief | No P1/public/WCAG certification claimed | NOT VERIFIED |
| EX-M01 — Public delivery / final release evidence | Critical to M5 | Current repo homepage null; deployments/releases empty; required human/host proofs incomplete | Hosting/account/authorization and finalization are not repository code alone | Follow existing deployment readiness audit; no production action performed | Current remote snapshot, local-only scope and live ledger | BLOCKED |

The added account lookup creates a read-only DB dependency on protected page
requests; database unavailability fails closed. Existing sanitized 503 handling
and lecturer HTML recovery are retained and tested. Cached-role rejection is
preserved, so a role change does not silently elevate a session. Current `/me`
returns database identity; automatic session/landing refresh after a role change
is not newly promised by this fix.

## Requirements versus observed behavior

| Requirement | Actual Behavior | Test Evidence | Status |
|---|---|---|---|
| US01 valid/invalid/unknown credentials and one of three roles | Existing canonical errors/session/role landing work; deleted account and downgraded-role gaps now denied | Existing auth suite, EX-A01/A02; real browser role landing and form error/focus test | PASS |
| US02 assigned list, five display details, search/filter/empty/status | Enrollment separation retained; previously merged team-teaching fix returns one row; normal/error/empty UI retained | Existing US02 cases including three active and EX-UX01 list recovery | PASS |
| Strict <24h Due soon and deadline <=now closed | Original approved boundaries unchanged; aware offsets checked deterministically | Existing boundary cases; controlled `<`→`<=` mutation fails only equality and is restored | PASS |
| US03 required fields, ratings/text boundaries, review/submit/receipt | Server refuses invalid/enrollment/deadline/duplicate requests; save/reload/cross-role persistence and concurrent-tab atomicity retained | Existing submission/database workflow tests; merged M5-A03/A04 plus EX-UX01 retry/no false success | PASS |
| US04 submitted-only feedback/count/rating/comment and ownership | Real lecturer browser list/detail/empty/error tests retained; downgraded role no longer receives feedback | Existing completed19/20/21/ownership tests, EX-A02 and role-mutation proof | PASS |
| US11 visible sign-out, denied protected access, Back and repeated logout | Student/lecturer/admin sign out; Back exposes only public login without restoring the typed password; repeated logout remains200; missing and over-age cookie denied | Existing keyboard/logout tests; EX-S01 (3 roles), EX-S02 actual signed-age expiry | PASS |
| Errors explain what happened and next action | Valid business messages unchanged; unreadable list/questions/submission replies now give fallback and working recovery | Six EX-UX01 cases plus existing network/permission/error tests | PASS |
| Preserve established UI/evidence/contracts/schema | No template/CSS/requirements/schema edits; four normal before/after captures identical under controlled conditions; no historical images modified | `ui-comparison.json`, source diff and eight newly named screenshots | PASS |
| Full existing regression suite retained | 298 baseline →318 final; new security/UX/clock assertions; no skip/deletion/expected-result weakening | Baseline/final JUnit and output; Ruff/diff checks | PASS |
| Tests can detect a broken business/security rule | Actual detached-worktree role mutation and temporary-export boundary mutation turn red, then restore green | `role-mutation.json`, `deadline-mutation.json`; workspace unchanged | PASS |
| Public HTTPS/private browser/physical phone/click-only deployed P0 | No verified origin/provider SHA supplied; local browser viewports do not satisfy public delivery | Current metadata and pending live ledger | BLOCKED |
| Real hosted persistence/health/logs/monitoring/rollback | Local safety/readiness/restart/restore tests pass; no hosted drill certified | Existing operations/runtime tests and deployment audit; actual platform evidence absent | NOT VERIFIED |
| Latest observed main CI green | Observed success for baseline0f924cd, not this future PR's merged candidate | [Main run43811819195](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43811819195) | PASS |
| Main requires PR+approval+green checks | Readable rulesets require approval but contain no named check; classic protection cannot be certified from prior404/non-admin read | Existing read-back and current rules snapshot; admin verification required | NOT VERIFIED |
| Deploy only after green | Gate/conditions/exact-SHA code and fake-provider failures tested; actual provider deployment not demonstrated | CI/deploy tests and prior real red-PR gate rehearsal; Deploy skipped | NOT VERIFIED |
| >=4 green reviewed Sprint5 PRs | Prior wrap-up has ten linked merged/green/independently approved PRs; #240–242 subsequently merged | Existing #212 snapshot plus current #242 state; not evidence of deployed acceptance | PASS |
| Substantive Review changes and per-member contribution evidence | Approval metadata is not automatically substantive; #242 approval body is empty; full fresh per-member certification not established here | Current approval snapshot and existing wrap-up evidence | NOT VERIFIED |
| Sprint5 wrap-up/sprint metrics | #212 currently CLOSED; log has all five sprints, but closure does not resolve absent planning/deployed/human evidence | GitHub #212 state; existing qualified five-sprint table | NOT VERIFIED |
| Releasev1.0 matches running SHA / final PDF / submission | No verified release/origin/SHA; draft/metadata remain pending; no submitted PDF certified | Current releases[], metadata, prior guarded draft builder and release checklist | BLOCKED |

These are scoped technical findings, not a numerical mark. The supplied M5 brief
makes the public working URL the deliverable; local tests alone cannot remove
that risk. Public timing must use the approved action-to-visible <=3,000ms
protocol, not pytest duration or local request timings.

## Test quality, iteration and provenance

1. Captured clean main SHA/baseline before edits: 298 passed in92.01s.
2. Added reproductions without changing old expected results: six deleted-account
   variants failed; real role downgrade returned200 instead of403; representative
   HTML503 showed a raw parser failure; two frozen-clock invariants failed.
3. Fixed only the shared access guard, unreadable-response paths and the incorrect
   shared test clock. Related checks: 137 access/data cases passed, six unreadable
   recovery cases passed, and96 clock/submission/smoke cases passed.
4. Continued beyond the first fixes: three role-history/expiry flows, repeated
   logout, actual signed-cookie age, and empty/invalid email keyboard-focus/retry
   checks. One *new test harness assumption* was corrected: admin Back can reach
   `/`, which is also the approved login page. It now asserts login content, no
   private controls and denied APIs rather than inventing a `/login`-only rule.
5. The first temporary screenshot script's route callback signature was corrected;
   the application was not changed to satisfy it. Final captures are deterministic
   and identical. External font stylesheet is neutralized equally before/after,
   with fixed clock/locale/viewport; this is controlled preservation evidence,
   not public-host font or physical-device certification.
6. Full post-fix regression: 318 passed in124.76s, zero failures/errors/skips.
   AST review found no duplicate module-level test-function names and no skip/xfail
   markers. An additional **279 non-browser API/DB/runtime/tool cases passed in
   reversed order in11.33s**; this is one extra ordering, not proof of every
   permutation. Existing assertions remain; only the shared mock clock's mathematically
   inconsistent timezone conversion was corrected, with a red reproducer.

Changed runtime files: `src/app.py`, `src/static/js/evaluations.js`,
`src/static/js/complete_evaluation.js`. HTML/CSS, `docs/requirements.md`, schema,
historical screenshots, working labels/navigation and production DB are untouched.
Normal list/question screens at1440×900 and390×844 have identical PNG hashes:
[comparison manifest](evidence/examiner/ui-comparison.json),
[phone before](evidence/examiner/ui/questions-390-before.png) /
[phone after](evidence/examiner/ui/questions-390-after.png).
Images were visually inspected; a full accessibility audit is not claimed.

## Evidence and reproduction

- [Baseline JUnit](evidence/examiner/baseline.xml) /
  [actual output](evidence/examiner/baseline.txt).
- [Final JUnit](evidence/examiner/final.xml) /
  [actual output](evidence/examiner/final.txt).
- [Deleted account red](evidence/examiner/deleted-account-before.txt),
  [role red](evidence/examiner/role-before.txt),
  [unreadable UI red](evidence/examiner/unreadable-before.txt),
  [fixture clock red](evidence/examiner/clock-before.txt).
- [Role worktree mutation](evidence/examiner/role-mutation.json):
  target passes → disabling current-role guard fails → restored passes;
  detached worktree removed, workspace source unchanged.
- [Due soon mutation](evidence/examiner/deadline-mutation.json):
  3 pass → equality1fail/2pass →3pass restored; main workspace unchanged.
- [Collection/duplicate-name review](evidence/examiner/test-collection-review.json)
  and [reversed API order](evidence/examiner/reversed-api-order.json) /
  [actual output](evidence/examiner/reversed-api-order.txt).
- [Review metadata/source hashes](evidence/examiner/review.json),
  [remote state](evidence/examiner/remote-state.json),
  [current live-evidence ledger](m5-live-verification.md).

```bash
python -m pip install -r requirements-dev.txt -r requirements-prod.txt
python -m playwright install chromium
python -m pytest -q --junitxml=junit.xml
ruff check .
git diff --check
```

This run uses the existing isolated macOS Python3.14.8/Playwright1.65.2 venv and
installed Chrome157 via PLAYWRIGHT_CHROMIUM_EXECUTABLE. Tests seed only temporary
synthetic SQLite; dangerous scenarios do not target production. No current DB
was reset, no historical evidence removed, no requirements/API/schema changed,
no self-review/merge/deploy/release executed. Independent teammate review and
fresh green CI are required before integration.

AI assistance: Codex — examiner review, scoped fixes and verification.
