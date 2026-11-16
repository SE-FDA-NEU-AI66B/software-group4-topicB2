# EduSurvey M5 deployment and release readiness

Audit: 2026-11-16, Asia/Ho_Chi_Minh. Baseline main:
`b26dfc896f679841be7da442edb1590a85a10bdd`. **Overall: BLOCKED for M5 submission.**
This branch prepares a reviewable release path; it does not deploy, publish a
release, change GitHub settings, modify a production database or certify a final
PDF. No UI, requirements, schema or P0 application behavior changes are included.

[Read-only GitHub/configuration evidence](evidence/m5-deployment-readiness.json)
records timestamps, main CI steps, permissions, rules and pending PRs. Empty
repository metadata does not rule out an unreported external host. No verified
public origin was found; no guessed Render hostname was tested.

## Current compliance matrix

PASS means the stated, scoped check was observed. FAIL means a known unmet
criterion. BLOCKED requires account access, authorization or missing information.
NOT VERIFIED means evidence has not been obtained; it never means passed.

| M5 Criterion | Current Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|
| Flask/Gunicorn production configuration | PASS | Existing runtime guards, production requirements/Procfile; config check and local HTTP smoke | Actual host startup | Reuse existing files; do not create a second server/API |
| Five P0 existing regression suite | PASS | Existing isolated API/database/browser cases remain green; final run below | Deployment verification and pending fixes | Keep local scope separate from public acceptance |
| Known P0 defects corrected on main | FAIL | [PR #241](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/241) still open at capture | Merge independent-reviewed fixes for duplicate list rows, receipt closure and concurrent submissions | Review/merge #241 and rerun main CI before selecting release SHA |
| Public HTTPS URL | BLOCKED | Repo homepage null; zero GitHub deployments; no supplied host origin | Account/service, cost approval, authorized initial deployment | Follow manual sequence below; do not present localhost as the app |
| Public private-browser/laptop/phone P0 | NOT VERIFIED | Local browser tests only | Actual HTTPS UI, allowed synthetic accounts, physical phone and persisted record | Fill the live verification ledger after authorization |
| SQLite startup and missing-data safety | PASS | Restart/missing-mount/corrupt/missing-provisioned DB tests; online-backup/restore checks | Actual mount | Retain fail-closed startup; never reset data on redeploy |
| Hosted reload/restart/redeploy persistence | NOT VERIFIED | Local reload/new-process proof is scoped below | Same saved record surviving real host lifecycle | Verify on mounted `/var/data`, not ephemeral source tree |
| Hosting configuration prepared | PASS | `render.yaml`: current `0.5c-512mb` plan ID, runtime startup guard, 1 GB disk, one instance, auto-deploy off | Provider-side validation/provisioning | Review actual billing and validate Blueprint in connected account |
| Main CI latest observation | PASS | [Run 43804267947](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43804267947) succeeded for baseline main | Fresh green CI on final merged candidate | Do not use this old run to certify a later commit |
| PR approval protection | PASS | Read-back: inherited organization PR rule requires one approval | Substantive teammate review of each new PR | Do not self-approve or self-merge |
| Required green checks enforced before merge | NOT VERIFIED | Ruleset read-back has no required_status_checks; classic protection endpoint returned 404 | Admin read-back of all protection mechanisms/screenshot | Confirm or enable CI gate, Python tests and No secrets committed, strict/up-to-date |
| Deploy-after-green code | PASS | `deploy needs: [gate]`; gate depends on detect/python/node/security; exact SHA and fail-closed tests | Actual green main → provider deployment | Keep Render auto-deploy off and use protected GitHub production environment |
| Live deploy-after-green rehearsal | NOT VERIFIED | Latest main Deploy skipped; GitHub Variables/environments empty | Real service ID, API secret, authorized release and provider history | Record both CI and provider commit identity |
| Sensitive tracked-file guard | PASS | Five previously missed filename variants reproduced; 12-case fix now passes | Independent PR review/merge | Block `.env.*`, DB/dump and key files even if force-added |
| Database-aware health and safe logs | PASS | Real local Gunicorn `/health` 200→503→200, missing file not recreated; privacy/readiness tests | Public health/log location/retention | Record host checks; existing monitoring policy remains |
| Hosted monitoring and rollback | NOT VERIFIED | Existing runbooks and local tooling; no hosted service evidence | Dashboard links, operator watch, backup transfer and rollback drill | Follow compatible-code rollback and incident procedure |
| README entry point | FAIL | Badge, demo credentials, P0 routes/team exist; URL still pending | Verified HTTPS origin on first line | Add actual origin only after live checks |
| Operations handover content | PASS | [operations.md](../operations.md), six ordered sections, risk/maintenance/lesson tables | Instructor section-count clarification and live evidence (#208) | Retain pending sign-off; use #240 follow-up rather than duplicate its edits |
| Five-sprint summary/velocity evidence | NOT VERIFIED | [sprint-log.md](../sprint-log.md) includes all five sprints; historical metrics qualified | Genuine planning/completion story-point records | Do not turn hours into velocity or invent attendance |
| v1.0 release/SHA identity | BLOCKED | Zero releases at capture; no deployed SHA | Reviewed green commit running at public URL and explicit publication authorization | Tag that exact deployed commit only after gates pass |
| Final Team04_M5.pdf | BLOCKED | Existing marked draft and guarded builder; URL/release/MSSV/confirmations pending | Confirmed IDs, live links, release, rehearsal/submission arrangement | Keep draft; no fake final PDF or upload claim |

## Work completed in this branch

1. Reused the existing Flask/Gunicorn, SQLite bootstrap, health/logging, backup,
   deployment orchestration, CI gate and draft submission tools.
2. Reproduced a CI guard defect: `.env.production`, nested `.env.local`, `.db`,
   `.pem` and `.key` could be tracked without triggering its filename rejection.
   Extended the guard, preserving reviewed SQL sources and `.env.example`.
   Twelve behavioral tests execute the actual workflow step in temporary Git repos;
   no real credentials or database files are used. Existing tests are retained.
3. Updated the reviewed Blueprint's compute plan identifier to the current
   documented `0.5c-512mb`; no resource was provisioned and no charge approved.
4. Added this audit, a pending live-evidence ledger and navigation links. Captured
   real GitHub metadata, local tests and a fresh Gunicorn smoke. Source/required
   checks were inspected without changing remote settings.

## Hosting choice and deployment configuration

Continue the existing proposal: one paid native Python Render web service in
Singapore, 1 GB persistent disk, one instance, one Gunicorn worker/four threads.
This preserves SQLite and same-origin UI/API requests with the least migration
work. A maintained VM with durable disk is an alternative but adds OS/TLS/backup
operations. A managed PostgreSQL design needs a reviewed migration and separate
approval; it is not a silent replacement for SQLite.

Render Free is unsuitable for this SQLite release: filesystem writes are lost
on restart/redeploy/spin-down, persistent disks cannot attach, and idle services
spin down after 15 minutes. See [official Free limits](https://render.com/docs/free).
Paid disks preserve only files under the mount and require a single instance;
they are unavailable during build/pre-deploy and remove zero-downtime deployment.
See [official disk constraints](https://render.com/docs/disks). The existing
runtime preparation is correctly in startCommand, not buildCommand.

The [current Blueprint reference](https://render.com/docs/blueprint-spec) lists
`0.5c-512mb` for 0.5 CPU/512 MB and `autoDeployTrigger: off`. This audit updates
the configuration identifier, not an existing live service. Disk storage is
listed at $0.25/GB/month; compute/workspace/usage costs are additional. The older
runbook's $7.25/month figure is a dated estimate, not a fresh account quote:
confirm [current pricing](https://render.com/pricing) in checkout before paying.
Provider-side Blueprint/account validation remains pending; local YAML parsing
alone is not provider acceptance.

| Setting | Location | Required value / handling |
|---|---|---|
| EDUSURVEY_ENV | Render environment | `production` |
| EDUSURVEY_DATABASE | Render environment | `/var/data/edusurvey.db` |
| EDUSURVEY_DATA_MOUNT | Render environment | `/var/data`, actual mounted disk |
| EDUSURVEY_SECRET_KEY | Render private environment | Generated stable random secret, >=32 characters; never paste into Git/chat |
| EDUSURVEY_BOOTSTRAP_DEMO | Render environment | `1` only for explicitly approved first synthetic setup on an empty new mount; set to `0` afterwards and reconcile Blueprint |
| PORT | Render supplied | Gunicorn uses `0.0.0.0:$PORT` |
| RENDER_API_KEY | GitHub environment `production` Secret | Private provider API credential, never a Variable or committed value |
| RENDER_SERVICE_ID | GitHub repository Variable | Actual selected `srv-…` ID |
| RENDER_DEPLOY_ENABLED | GitHub repository Variable | Initially `false`; `true` only after authorization/configuration/read-back |

Build: `pip install -r requirements-prod.txt`. Start:
`python -m tools.prepare_production && gunicorn --config gunicorn.conf.py src.app:app`.
Health path `/health`; persistent mount `/var/data`; platform auto-deploy off.
Canonical synthetic accounts are in [README](../../README.md#disposable-demo-accounts).
No new production account or seed was created by this audit.

## CI/CD verification and settings handoff

Required flow: PR → independent review + green PR CI → merge main → green main
CI → exact-commit deploy → provider SHA/HTTPS verification. The current read-only
GitHub actor can push and read effective rules but has no administrator permission.
Rulesets therefore could be inspected; settings changes remain BLOCKED, not performed.
The classic branch-protection API returned 404. That can mean absent protection
or unavailable access, so overall named-check enforcement is NOT VERIFIED rather
than inferred absent from the ruleset response alone. An administrator must confirm
both legacy protection and rulesets before changing settings.

| Pipeline job | Verified configuration/behavior |
|---|---|
| Detect stack | Checkout and manifest detection |
| Python tests | Python 3.12; dev+prod dependencies; Gunicorn config; Chromium/system dependencies; blocking Ruff; full pytest/browser suite; JUnit summary |
| Security | Credential-pattern scan and tracked sensitive-file rejection; source/schema/template exceptions retained |
| Node | Conditional, skipped for this Flask repository; its existing warning-only lint is not described as a blocking Python check |
| CI gate | Always evaluates detect/Python/security and detected Node; required failure/cancel/skip rejects the gate |
| Deploy | `needs: [gate]`, success semantics, main push only, explicit opt-in, production environment; rejects superseded main before contacting provider; one serialized production job |

`tools/deploy_render.py` checks the selected service's repo/main/disabled automatic
deploys, requests `commitId=GITHUB_SHA`, polls one deployment ID, compares its live
commit and checks HTTPS health. Fake-provider tests verify failure paths but do
not prove Render connectivity. Latest green main took **118 seconds** from run
start/update timestamps; its Deploy job was **skipped**, not successful hosting.
Every observed job/step is in the evidence JSON. No new deliberately red PR was
published: the existing [#207 red rehearsal](../ci-production-gate.md) is retained.

Administrator action, not executed here: Settings → Rules → Rulesets → reviewed
[main-ci-protection configuration](../../.github/main-protection.json), active for
main; PR + >=1 approval, latest-push/stale-review controls, strict required checks
`CI gate`, `Python tests`, `No secrets committed` from GitHub Actions. Read back
actual effective rules and capture a new screenshot. Follow
[administrator handoff](../main-protection-admin.md). Do not bypass organization
rules, expose a token or call the helper's `--apply` without authorization.

## Database persistence and recovery strategy

Only `/var/data/edusurvey.db` is authoritative on the host. Existing startup
preparation verifies the real mount, schema/integrity/FKs and provision marker.
A missing previously provisioned DB fails closed and requires recovery; it is
not auto-reseeded. Existing data/deadlines are not refreshed by restarting.
The first initialization requires explicit synthetic-demo opt-in and refuses
to overwrite a file. Never initialize live data manually during a redeploy.

Local suite evidence covers browser reload, new process reads, byte-preserving
startup, missing/corrupt/mount failures, online backups and isolated restore
comparison. These tests use temporary data; some mount/provider conditions are
mocked. **Actual Render restart/redeploy preservation remains NOT VERIFIED.**
For the live drill, record a permitted synthetic response ID/count at the exact
provider SHA, reload, restart, redeploy, and verify that same record, health and
relationships after each stage. Preserve results in the ledger; don't reset the
DB to manufacture an empty submission slot. Follow
[database procedures](../database-operations.md).

Back up with the existing SQLite online backup tool, validate in isolation and
transfer an encrypted/access-controlled copy off-host. Copying a live DB file or
restoring a raw disk snapshot is not the prescribed DB recovery method. Actual
scheduled backups, retention access and off-host restoration need operator proof.

## Monitoring, availability and rollback

[Monitoring](../monitoring.md) defines sanitized app stderr events: UTC time,
server-generated request ID, endpoint, method, status and monotonic duration.
Passwords, cookies, bodies, raw queries and personal feedback are excluded.
Gunicorn raw access logging is off. On a real service use Render Logs/Metrics;
record actual service links, access and retention. Provider logs need their own
privacy check. `/health` is 200 for ready data and sanitized 503 on missing/corrupt/
locked/incomplete data; no replacement DB is created. Local network smoke
observed 200→503→200, not a public uptime result.

Owner Đức Anh watches every minute during release/demo. Investigate any failed
health check immediately; use five-minute error rate >=5% and server p95 >1,000ms
when N>=20, with definitions/exclusions in the existing monitoring contract.
Five consecutive latency breaches trigger investigation/rollback coordination
with Huy. Outside watch, follow the documented daily/manual policy; unattended
alerts are not verified. Server durations do not prove the inclusive 3,000ms
browser-action-to-visible-outcome P0 requirement.

Rollback procedure, pending real rehearsal:

1. Record incident, last known healthy provider deploy ID/full SHA, matching green
   CI, release identity, schema compatibility and validated off-host backup. The
   last main commit alone is not a last-known-good deployment.
2. Coordinate with the operator; disable future CI release opt-in and confirm no
   active deploy before an approved rollback. Keep platform auto-deploy off.
3. Use the previous compatible retained build through Render Deploys → Rollback;
   record the target provider SHA. If unavailable, prepare a reviewed revert PR,
   green main CI and authorized exact-SHA deploy instead. Do not rewrite Git history.
4. Preserve the disk/data. Code rollback does not reverse a DB migration or restore
   rows. If data recovery is needed, stop writers and restore a validated backup
   to an isolated candidate under the existing recovery runbook; do not overwrite
   the live DB as part of this audit.
5. Verify provider SHA, HTTPS `/health`, login/roles, existing saved response and
   lecturer feedback; retain timings/logs and re-enable CI release only after
   operator confirmation.

Render rollback retention is plan-dependent; dashboard rollback disables its
automatic deploys, API rollback does not, and disks retain current state.
See [official rollback behavior](https://render.com/docs/rollbacks). No dashboard
rollback, restart or redeploy was performed here.

## Release identity, README and final PDF

Before publication, merge reviewed fixes/audit PRs and select a **specific tested
main commit actually running at the approved HTTPS origin**. Compare full provider
commit, successful main CI SHA and future dereferenced `v1.0` commit. Never tag a
newer main while deployment lags; do not move an existing tag to conceal drift.
Existing [v1.0 checklist/commands](../m5/release-checklist.md) and exactly three
[summary lines](../m5/v1.0-notes.txt) are prepared. **No tag or release is created.**

README already contains CI badge, demo accounts, five P0 entry paths and team
names; its missing public first-line URL remains a FAIL until verified. The
operations handover is implemented, with #240 updating review evidence. Its
instructor six-versus-seven-section clarification and deployed facts remain
pending. Sprint log includes five sprints; unknown/historically inconsistent
story points and velocity must not be replaced with task hours.

Team 04 and Scrum Master Khuất Đình Trung are confirmed. Member names are present;
student IDs, actual app/release URLs and human/course confirmations remain
pending in [submission metadata](../m5/submission.json). Existing marked
[Team04_M5_DRAFT.pdf](../m5/Team04_M5_DRAFT.pdf) is a preview, not a submitted/final
PDF. A fresh `--final --pdf` attempt exited **2** before export with this real pending metadata; no final PDF was created. After verified
release, update actual URLs/full SHAs/latest green main CI and confirmed IDs,
rebuild the final PDF, inspect every link and its first line `Running app: …`.
A generated file is not an LMS submission; uploading needs separate authorization.
Confirm real late-submission/keep-online arrangements, not an invented deadline.

## Required manual actions, in order

1. Review/merge #241 and the relevant docs/audit PRs with independent review; wait
   for the final candidate's successful main CI. No self-merge is performed here.
2. Repository admin enables/read-backs the named-check rules and production
   environment controls. Keep the deploy flag off until release authorization.
3. Choose the hosting account and explicitly approve cost and the initial public
   deployment. Until then **do not click Blueprint Deploy/Create**: first service
   creation itself can deploy even with platform auto-deploy off.
4. Connect that account to this GitHub repository, validate the reviewed Blueprint,
   select the paid plan/disk/region and review the actual checkout quote. Provision
   only the approved new service, with the environment checklist above. Do not
   substitute Free/ephemeral SQLite or silently migrate to PostgreSQL.
5. Verify stable secret, actual mount, startup guard, service ID and first provider
   SHA. Disable bootstrap afterwards and reconcile its Blueprint setting. Keep
   demo data synthetic and never reseed existing data.
6. Store API key privately in GitHub production Secrets; configure nonsecret
   service ID and release flag. Confirm platform auto-deploy off. After explicit
   go-ahead, permit a green main push to release through the gate; record exact SHA.
7. Provide the real HTTPS origin/provider view. Execute the live ledger's private
   desktop/phone P0, persistence/health/logs, deterioration and approved rollback
   checks, including real browser timings. No submitted real-student data.
8. Resolve instructor/identity/contribution/retention information. After the SHA
   and evidence gates pass, obtain explicit tag/release approval, publish exact-SHA
   v1.0, finalize README/PDF, verify links, then use authorized course upload.

## Test evidence and limitations

Final regression results are recorded below after execution. Commands:

```bash
python -m pip install -r requirements-dev.txt -r requirements-prod.txt
python -m playwright install --with-deps chromium
python -m pytest -q --junitxml=junit.xml
ruff check .
gunicorn --check-config --config gunicorn.conf.py src.app:app
git diff --check
```

This macOS run uses the existing isolated venv and installed Chrome selected via
PLAYWRIGHT_CHROMIUM_EXECUTABLE; browser servers and databases are temporary.
YAML parsing/configuration tests, missing-DB/health/privacy tests, startup and
backup/restore tests, gate rejection cases and all browser E2E are included.
Local scans execute the credential pattern without exposing values and the new
tracked-file guard. These are limited checks, not a comprehensive secret-history
or security certification. PR CI must independently pass the committed changes.

**Final local result:** **290 passed in 81.61s**, zero failures/errors/skips,
after the final CI/Blueprint changes. Twelve new security filename variants are
included; this count is for baseline main plus this branch, not unmerged #241.
Ruff, Gunicorn config, YAML/config checks, limited secret/filename scans, local
links and diff checks passed. [JUnit](evidence/m5-readiness-pytest.xml),
[actual output](evidence/m5-readiness-pytest.txt),
[pre-fix red cases](evidence/sensitive-files-before-fix.txt) and
[local network smoke](evidence/m5-readiness-gunicorn.json) are retained.

[Live verification ledger](m5-live-verification.md) intentionally retains PENDING
for unobserved hosted/human checks. Historical documents and draft evidence remain.
AI assistance: Codex — deployment/configuration review and verification.
