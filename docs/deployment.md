# EduSurvey deployment - #205

Status (2026-11-15): **repository setup prepared; no hosted service or public URL
has been provisioned/verified**. Parent #200; coordinate storage #204, CI/main
protection #207 and deployed P0 verification #210. Actual hosting-account access,
paid-resource approval and the instructor's keep-online date are pending.

## Selected design and cost review

Proposed platform: Render, one Python web service in Singapore with a 1 GB
persistent disk, one Gunicorn worker/four threads. Flask serves HTML and same-origin
relative API URLs, so no second frontend/CORS configuration is required.
`render.yaml` is a reviewable proposal; committing it does not provision a service.

Official pricing checked 2026-11-15: smallest paid compute is $7/month and disk
is $0.25/GB/month: approximately **$7.25/month base** for this proposal, excluding
taxes, bandwidth/build overages or paid workspace choices. Confirm the actual
checkout price/account limits before purchase. No paid resource was created.
[Pricing](https://render.com/pricing), [disk terms](https://render.com/docs/disks).

Free services cannot attach persistent disks, lose filesystem changes on
restart/redeploy and spin down after 15 minutes idle, with 750 workspace free
instance hours/month. This persistent SQLite proposal therefore uses paid compute.
There is no claim of a measured cold-start bound or <=3,000ms public interaction.
Disk-backed services have a single instance and deployment downtime; do not
promise zero-downtime releases. [Free limits](https://render.com/docs/free),
[disk limitations](https://render.com/docs/disks#disk-limitations-and-considerations).

## Provisioning and secrets

1. Connect the selected Render account and authorize access to this repository.
   Review/approve the paid service/disk before creating the Blueprint. Use a
   reviewed, green main commit for initial provisioning; initial service creation
   itself is a manual deploy and must not be represented as automated gate proof.
2. Apply `render.yaml` after its reviewed merge. `autoDeployTrigger: 'off'` is
   required: platform push hooks must not bypass the GitHub gate. The build installs
   `requirements-prod.txt`; startup prepares the persistent DB then runs the
   existing Gunicorn config bound to `0.0.0.0:$PORT`.
3. Render generates a stable `EDUSURVEY_SECRET_KEY` in service settings, not Git.
   `EDUSURVEY_ENV=production` enables existing secret/path guards and Secure cookies.
   Database `/var/data/edusurvey.db` must reside on the actual `/var/data` mount.
4. `python -m tools.prepare_production` refuses a missing mount, corrupt/incomplete
   existing database or a missing previously provisioned database. Only the first
   absent DB with explicit `EDUSURVEY_BOOTSTRAP_DEMO=1` can seed synthetic accounts.
   A persistent `.edusurvey-provisioned` marker prevents accidental reseeding after
   later DB loss. Existing data/deadlines are not refreshed on restart. Recovery
   and migrations follow [backend runtime handover](backend-runtime.md).
5. Once the first DB is healthy, set `EDUSURVEY_BOOTSTRAP_DEMO=0` in the platform
   settings and reflect it in the reviewed Blueprint so sync cannot re-enable it.
6. Create GitHub environment `production`; put `RENDER_API_KEY` in its Secrets.
   The account/API token must have only the provider permissions necessary for
   reading the selected service and deploying it. Keep values out of chat/logs.
   Repository Variables: `RENDER_SERVICE_ID` (the real srv- ID) and initially
   `RENDER_DEPLOY_ENABLED=false`. After service/config verification, set the flag
   to `true`. Neither variable contains a credential.

No exposed production credential was observed or revoked by this task. Public
synthetic demo passwords are not production service/API secrets. If an actual
secret is exposed, revoke it at the provider and replace the stored setting.

## Green-gated releases

The deploy job is in the **same CI workflow** as the real Python test/security
jobs, with `needs: [gate]` after merged #207. The gate requires successful
detection/Python/security and any detected Node stack. Default success semantics
prevent deployment if a required job fails, is canceled or skipped. PRs, feature pushes
and a disabled deployment flag cannot release. Existing full pytest and both
security scans are retained. Node is not part of the current Flask stack.

The main workflow is serialized without canceling an in-flight release; other
branches retain cancellation. Before provider access, the job verifies its SHA
is still current main. It checks out that exact SHA, uses the protected production
environment and calls `tools/deploy_render.py`. The helper refuses PR/non-main
contexts and a service with automatic deploys enabled or wrong repository/branch.
It submits `commitId=GITHUB_SHA`, polls a bounded deployment ID, compares the live
provider commit and checks public HTTPS `/health` JSON. No floating latest deploy
hook is used. A timeout is a failure requiring dashboard inspection, not a retry
that blindly creates more deploys. [Render exact-commit API](https://api-docs.render.com/reference/create-deploy).

An admin/owner must apply and verify the independent #207 PR/approval/required-
check branch protections. This commit does not grant those protections or turn
mock API tests into proof that the provider account is configured correctly.

### Required real gate rehearsal - pending

The isolated negative-PR part has since been executed: [#207 evidence](ci-production-gate.md)
records closed/unmerged PR #231 with a real failed suite/gate and skipped Deploy.
The steps below remain the host-account/provider verification procedure, not
proof that a reviewed green merge actually deployed. #208's
[operations handover](operations.md) separates these observed and pending states.

After setup, record service/deploy history and the latest green main SHA. Create
an isolated draft PR with a deliberately failing pytest assertion; never merge
it. Link the real failed Python job and skipped Deploy job, and verify no provider
deployment for that candidate SHA. Close/delete the probe branch after preserving
the run URL/evidence. Then a reviewed green merge must show successful dependency
jobs, the exact deployed SHA and working HTTPS `/health`. Coordinate this drill
with #207. No deliberately broken production commit is required or authorized.
These steps are planned, not executed evidence.

## Rollback and post-release checks

Before each release record the previous healthy deploy ID/SHA, current schema
compatibility and an off-host SQLite online backup (existing helper). For an
incident use Render Deploys > previous successful deploy > Rollback, then verify
the provider SHA, HTTPS `/health`, student/lecturer access and an existing seeded
record after reload. Keep the persistent disk intact; an application rollback
does not roll back database schema/data. Never run the destructive initializer.

Dashboard rollback disables platform autodeploys, which must remain off. Also set
`RENDER_DEPLOY_ENABLED=false` before the drill/incident so queued future main runs
do not supersede the rollback. Fix through a reviewed green PR, then re-enable the
CI flag after verification. If no retained compatible build exists, use a reviewed
Git revert and green main CI. [Render rollback behavior](https://render.com/docs/rollbacks).

This is a runbook, not a claim that a hosted rollback was exercised. Capture two
successful deployment IDs first, then perform the real drill and record results.
Test private desktop and phone HTTPS flows, a saved response after reload and
restart/redeploy, and the actual SHA before marking #205/#210 complete.

## Evidence register

| Requirement | Current evidence / remaining work |
|---|---|
| Gunicorn bind and environment guards | Existing #223 runtime reused; Blueprint invokes it |
| Preserve DB on restart | Temporary DB byte-for-byte restart test; actual mount/redeploy still pending |
| Missing mount/DB or corrupt data | Focused startup tests reject without resetting data |
| Pin deploy and reject wrong configuration/SHA | Fake-provider orchestration tests; not a live provider drill |
| Failed real test prevents deploy | Workflow dependency configured; actual Actions/provider rehearsal pending |
| Stranger can open HTTPS on desktop/mobile | Pending account, paid-resource approval and service creation |
| Rollback exercised and reverified | Pending actual previous deploys/service access |
| Keep online until grades | Date unknown; task owner does not know it. Instructor confirmation required; no invented shutdown date |
| Independent review / main protection | #207/admin and teammate review pending |

Focused local Windows/Python 3.12.6 verification:
`python -m pytest -q tests/test_deployment.py` -> **10 passed in 0.44s** after the
final initializer-global cleanup. Changed Python files passed Ruff. Both YAML
files parsed, dependency/security-step/mount configuration checks passed, and
`git diff --check` passed. No public URL, charged resource, failing-test deploy
block, hosted restart or rollback result is claimed by these local checks.

### Integration findings while preparing the gate

Main 686bd9e contained stale #189 FK-OFF/exception assertions after #223's runtime
fix and two Windows-incompatible #223 test assumptions. The initial full run had
5 failed / 195 passed. Existing nodes were updated to assert actual FK-ON orphan
rejection, sanitized 503 with exact rollback/retry, a genuinely absolute tmp_path,
and backup creation mode 0600 with effective mode-bit enforcement on POSIX.
No failing test was skipped or production rule relaxed. Windows ACL privacy
remains a separate operator responsibility. Focused integration verification:
53 passed in 5.01s; see docs/testing.md for traceability and full results.

Final full local verification (Windows/Python 3.12.6, installed Chrome selected via
PLAYWRIGHT_CHROMIUM_EXECUTABLE): `python -m pytest -q --junitxml=junit.xml` ->
**200 passed in 118.32s (0:01:58)**, zero failures/errors/skips. This includes the
existing 190 collected cases on main 686bd9e and ten new deployment cases.
Real hosting, paid-resource approval, CI red-test gate proof, rollback and release
verification remain pending; a local green suite does not complete #205.
