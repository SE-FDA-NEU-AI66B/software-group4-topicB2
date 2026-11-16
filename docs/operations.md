# M5 operations handover — #208

Parent #200; dependencies #204–#207 are merged. This is a reviewable repository
handover, **not production sign-off**. Instructor confirmation of “seven sections”
versus six enumerated sections is **pending**; six are retained without inventing
a seventh. Public URL and hosted rollback remain unverified. PR #233 is merged
with independent approval and substantive PR discussion; see the linked register. [Evidence and outstanding confirmations](evidence/208/README.md).

## 1. URL, platform, release and rollback

| Item | Observed state / operating procedure |
|---|---|
| Public HTTPS URL / deployed SHA | Not verified; #205/#200 must supply actual URL, service ID, provider SHA and private desktop/phone results. A closed issue is not deployment proof. |
| Platform/storage | `render.yaml` proposes paid Render, one instance/worker, four threads, mounted `/var/data/edusurvey.db`; no account/mount confirmation. Ephemeral SQLite is not durable. [Database runbook](database-operations.md). |
| Release | Reviewed PR → green main `CI gate` → deploy only with `RENDER_DEPLOY_ENABLED=true`, production Secrets and exact/current SHA → provider SHA + HTTPS `/health` verification. Platform auto-deploy stays off. |
| Observed deployment configuration | GitHub Variables/environments/deployments were empty at audit. This does not rule out an unreported external service; no live release is certified. |
| Rollback method | Open a reviewed revert PR restoring the last compatible good code; green main follows the same deployment gate. Preserve SQLite data; verify health, roles and saved response afterward. Hosted rehearsal pending #205. |

Before rollback, record source/target SHAs, schema compatibility and a validated
off-host backup. Restore only to an isolated candidate with writers stopped;
never reseed live data. [Deployment procedure](deployment.md).

## 2. CI, duration and branch protection

Latest observed green main: **`b26dfc8`**, [run 43804267947](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43804267947).
Actual elapsed time: **118s**, 2026-11-16 11:28:05–11:30:03 ICT, from GitHub
run-start/update timestamps. Job durations overlap; they are not summed.
[Current steps/timestamps and review](evidence/208/followup-audit.json);
[original audit](evidence/208/handover-audit.json) remains historical.

| Job | Every configured step, including lifecycle | Observed result/time |
|---|---|---|
| Detect stack | Runner setup; checkout; detect Python/Node manifests; checkout cleanup | Success, 6s |
| Python tests | Checkout; Python 3.12/pip cache; upgrade pip; install dev+prod requirements; Gunicorn config check; managed Chromium/system dependencies; blocking Ruff; full pytest `-v --cov --cov-report=term-missing --junitxml=junit.xml`; always publish JUnit summary; cache/checkout cleanup | Success, 92s |
| Security | Full-history checkout; credential-pattern scan; reject `.env`/DB dumps with existing schema/query exceptions; cleanup | Success, 8s |
| Optional Node | Checkout; Node 20/npm cache; `npm ci` or install; lint, test, build when present; cleanup. Node lint remains warning-only. | Skipped: no Node stack |
| CI gate | Checkout; always evaluate detection/Python/security and detected Node results; fail closed on required failure/cancellation/skip; cleanup | Success, 8s |
| Deploy | Exact-SHA checkout; Python 3.12; reject superseded main; provider configuration check, exact-commit deploy, bounded polling, SHA/readiness check; cleanup | Skipped: deployment opt-in absent |
| Other PR workflows | Scrum issue link/reviewer-participation/size checks; Board status automation | Informational process checks; not approval or deployment evidence |

[Actual GitHub rules screenshot](evidence/208/main-rules.png) shows PR plus one
approval; required named checks are **not enabled**. Administrator action is
still needed for `CI gate`, `Python tests`, `No secrets committed`.
[Apply/read-back handoff](main-protection-admin.md). Tokens stay read-only for
CI; provider credentials belong only in production Secrets. Approval is separate
from a passing workflow. [Real red-PR refusal](ci-production-gate.md).

## 3. Logs, health and deterioration detection

App stderr emits UTC time, generated request ID, endpoint, normalized method,
status and monotonic duration; ERROR records correlate by request ID. Raw
URLs, credentials, cookies and answers are omitted. Gunicorn raw access logs
are disabled; provider/dependency logs require separate privacy review.

| Operator check | Procedure and verified limit |
|---|---|
| Read logs/resources | Planned Render service → [Logs](https://render.com/docs/logging)/[Metrics](https://render.com/docs/service-metrics). Actual service URL/access and log retention are pending #205; plan-specific graphs are supplementary. |
| Health | `GET /health`: healthy app/SQLite → 200; missing/corrupt/incomplete/FK-invalid/locked DB → sanitized 503, no replacement file. [Real isolated HTTP 200→503→200](evidence/206/local-health.json); public HTTPS check pending. |
| Real public check | Once URL is supplied, run `curl -i "$PUBLIC_URL/health"`; retain UTC time, provider SHA, status/body and `X-Request-ID`; configure host HTTP health path `/health`. |
| Error rate | `100 × count(status>=500)/N`, five-minute `(now−300s,now]` window; exclude health/static, include redirects/4xx; investigate ≥5% when N≥20. |
| Response time | Nearest-rank server p95, `ceil(.95×N)`; investigate >1,000ms when N≥20. Server time excludes network/rendering and does not prove the 3,000ms browser criterion. |
| Notice/escalate | Duc Anh manually checks every minute during release/demo watch. Any health failure: inspect immediately. Five successive latency breaches: coordinate rollback/investigation with Sy Huy; record incident. Unattended alert delivery is unverified. |

Aggregate exported app-message text with `python tools/summarize_requests.py`.
Exit 2 means a threshold breach, not a delivered notification. Low sample,
invalid/duplicate events and missing log coverage prevent confident conclusions.
[Detailed contracts and historical evidence](monitoring.md).

## 4. Risks and technical debt

| Item | Layer | What could happen | Plan |
|---|---|---|---|
| SQLite writer contention | code | Concurrent writes time out/return 503 | Sy Huy: keep single-instance design; inspect lock failures; scale/migrate only through reviewed compatibility work, [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200)/[#204](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/204). |
| Only local/provider-fake release evidence | tests | Public P0 flow or rollback fails despite green CI | Duc Anh: record actual HTTPS desktop/phone, SHA and rollback under [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200)/[#210](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/210). |
| Ambiguous section count | docs | Handover misses instructor intent | Trung obtains written instructor interpretation; Sy Huy retains link/answer under [#208](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/208) before compliance sign-off. |
| Unverified mount/off-host backups | data | Restart or volume loss loses submissions | Sy Huy: confirm mount, execute backup/restore/secure transfer; [#204 policy](database-operations.md), remaining evidence [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200)/[#205](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/205). |
| Missing required named checks | infrastructure | A reviewed red PR could still merge | Administrator applies/re-reads [#207](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/207) rules; Sy Huy records updated screenshot under [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200). |
| Hosting/retention unconfirmed | infrastructure | Service unavailable before grading | Trung confirms keep-online date; Duc Anh confirms account/plan and operating access, [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200)/[#205](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/205). |

## 5. Maintenance ownership and frequency

Assigned policy below is not a claim that remote scheduling or alerting exists.

| Area | What to do | Owner | How often |
|---|---|---|---|
| Bugs | Correlate request ID, triage issue, reproduce with fake data; review fix before deploy | @tlduongducanh281-jpg | Daily triage; immediately for readiness/security incidents |
| Dependencies | Review updates/advisories, install dev+prod, full CI and compatibility checks in PR | @lesyhuy2k6-gif | Weekly and before release |
| Backups | Online snapshot to `/var/data/backups/`; secure off-host `~/EduSurveyBackups/`; verify real archive/access; retain 7 daily/4 weekly copies | @lesyhuy2k6-gif; deputy @tlduongducanh281-jpg | Manual daily 00:30 ICT and pre-release/migration; isolated restore weekly and before launch |
| Monitoring | Health/log watch and five-minute aggregation; record breaches, gaps and response; arrange handover when absent | @tlduongducanh281-jpg | Every minute during active release/demo; daily otherwise; automation pending |
| Docs | Update URL/SHA/runbook/evidence; obtain instructor clarification and independent substantive review | @lesyhuy2k6-gif; instructor liaison @khuatnhatminhcfpro-cmyk | Every deployment/change; weekly review |

## 6. Lessons from actual work

| What happened | What changed | What to do differently |
|---|---|---|
| [#190 clean clone](m4-review-evidence.md) found five failures after backend integration | Updated FK-ON/sanitized-503 contracts and Windows fixtures; retained rollback/retry assertions | Reconcile contracts and run clean integration before calling merged test totals evidence. |
| [#204 merge runs](evidence/204/README.md) timed out on fetched questions/review | Added explicit loaded-form waits and selected-rating assertions; retained both failing logs and green rerun | Await observable data preconditions, not navigation alone; never hide failures with skips. |
| [PR #231](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/231) deliberately failed one case | Actual CI gate failed and deploy skipped; closed without merge | Rehearse refusal on an isolated PR and distinguish it from a real provider rollout. |
| [Rules audit](evidence/208/handover-audit.json) found approval-only main protection | Prepared strict named-check rules and admin handoff; enforcement still pending | Read settings back and capture actual screenshots; green CI alone does not protect main. |

Sign-off still requires instructor clarification, actual deployment/rollback,
and updated protection evidence. PR #233 has independent approval and concrete
PR discussion; it does not establish live acceptance or the separate #212
requirement for substantive feedback through Review changes.
