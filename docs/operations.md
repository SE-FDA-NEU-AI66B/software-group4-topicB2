# Operations: health and request monitoring (#206)

Scope: parent #200 and database dependency #204. This is the implemented
health/monitoring handover; the broader #208 operations deliverable still needs
its own review. **Public service, account access, live health URL and real alert
delivery are pending #205.** No production outage or observed production metrics
are invented here.

## Health contract and safe demonstration

| Request/check | Result | Meaning |
|---|---|---|
| Anonymous `GET /health`, schema queries + SQLite quick_check + foreign_key_check succeed | 200 `{"status":"ok","database":"ok"}` | Current app/read readiness |
| Missing/empty/corrupt DB, missing required table, orphan FK rows, exclusive-lock timeout | 503 `{"status":"unavailable","database":"unavailable"}` | Database cannot satisfy readiness check |
| Every health result | `Cache-Control: no-store`; generated `X-Request-ID` | Avoid stale green probes; correlate safe logs |

The database is opened read-only with a two-second SQLite lock timeout and is
always closed. A missing file is never replaced with an empty DB. The check
queries required tables rather than returning unconditional 200. It does not
write rows, certify write throughput/disk capacity, or repair data. SQLite
integrity checks have workload-dependent duration; no latency bound is claimed.

Run the isolated demo cases (temporary SQLite only):

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v tests/test_backend_runtime.py::test_health_database_check
python -m pytest -v tests/test_monitoring.py::test_health_rejects_unusable_database
```

The second command for monitoring copies a seeded temporary DB before dropping a
table, inserting an orphan, or holding an exclusive lock. It verifies sanitized
503 and then healthy 200 after pointing back to the untouched temporary seed DB.
Never reproduce these failures on the deployment's database.

After #205 provides a verified URL, set `PUBLIC_URL` to that actual HTTPS origin
and run `curl -i "$PUBLIC_URL/health"` from outside the hosting network. Open the
same URL in a fresh desktop/private and phone browser. Record service ID, deployed
SHA, timestamp, response status/body and request ID. Do not replace an absent URL
with localhost in released evidence. A safe local HTTP rehearsal is labeled local
in the evidence register below; public verification remains pending.

## Sanitized event schema

The production app emits INFO `request_completed` and ERROR records to stderr.
Gunicorn raw access logging is disabled by the existing config; production
Werkzeug access logging is suppressed. Logs produced by a hosting proxy or other
dependencies require a separate privacy/retention review.

| Field | Source and purpose |
|---|---|
| `timestamp` | UTC ISO-8601 completion/error time for windowing; host clock must be synchronized |
| `request_id` | Fresh 32-hex server-generated ID; ignores inbound X-Request-ID and appears in response header |
| `endpoint` | Flask endpoint name or `unmatched`; never raw URL, path parameter or query string |
| `method` | Standard HTTP verb or `OTHER` for unrecognized input |
| `status`, `duration_ms` | Completion HTTP status and monotonic time from Flask before_request to after_request |
| `event`, optional `error_type` | Internal category and exception class, without exception message or stack dump |

Error categories include `request_failed`, `database_unavailable` and
`feedback_database_unavailable`. They share the request ID of the completion
record, allowing diagnosis without exposing credentials, connection strings,
paths, names, emails, tokens, cookies, authorization headers, request IDs supplied
by clients, answers or request/response bodies. Do not enable debug/raw dumps.
Request IDs are per request, not stable user/session identifiers.

Server duration excludes network, browser rendering/navigation, reverse-proxy
queue time before Flask and streamed-body delivery after after_request. It is
not the M5 <=3,000ms action-to-visible-outcome measurement or a replacement for
deployed browser verification.

## Calculations and thresholds

`tools/summarize_requests.py` reads one app-message line at a time from stdin
(pure JSON or a textual prefix followed by the app JSON). Supply exported
**message text**, not a provider API envelope or screenshot. The tool outputs
aggregate JSON only, never copies invalid/private input into its report.

| Measure | Window/method | Investigation threshold / action |
|---|---|---|
| Interactive request sample | Completion timestamps in `(now-300 seconds, now]`; exclude `health` and `static`; include redirects and 4xx | Fewer than 20 requests is low sample, not proof of good health |
| Error rate | `100 * count(status >= 500) / interactive_count` | >=5% with at least 20 requests: investigate immediately |
| Server p95 | Sort durations; take 1-based item `ceil(0.95 * count)` (nearest rank) | >1,000ms with at least 20 requests: inspect; sustained breach at five successive one-minute reviews escalates |
| Readiness failure | Separate count of health completions with status >=500, never diluted into interactive denominator | Any failure: check mount/storage/deployment immediately; do not reset live data |
| Missing/invalid log data | Empty denominator yields null rate/p95; invalid event and duplicate counters reported | Fix export/collector/clock gaps before claiming observations are representative |

All 4xx are excluded from the server-error numerator but remain in the denominator.
Duplicate request IDs within the window are counted once; future and exact lower-
boundary timestamps are excluded. Nonfinite/negative duration, malformed status,
missing/naive time and malformed request ID are rejected. The tool reports
`low_sample`, `invalid_events` and `duplicate_events`; dropped or incomplete logs
can bias metrics. Thresholds are operational policy, not measured production
results. CLI exit 2 means a threshold crossed, 0 means no configured breach in
the supplied data; neither means an external notification was delivered.

```bash
# On host: run the existing production command with configured environment.
gunicorn --config gunicorn.conf.py src.app:app 2> runtime.log
# Aggregate an exported/safely stored log file; defaults to current UTC.
python tools/summarize_requests.py < runtime.log
# Deterministic replay of an old window (use its real captured time).
python tools/summarize_requests.py --now 2026-11-15T12:00:00+00:00 < runtime.log
```

PowerShell equivalent: `Get-Content runtime.log | python tools/summarize_requests.py`.
Keep raw exported logs out of Git/public artifacts and retain them only under the
agreed operator policy. The committed synthetic summary is an example, not a
production observation.

## Where to read and who investigates

Proposed platform remains Render. Responsible member: @tlduongducanh281-jpg
(#206 owner). After service access is provisioned, open
[Render Dashboard](https://dashboard.render.com), select the actual EduSurvey
service, then **Logs** for runtime stderr and **Metrics** for resource usage.
Select a five-minute time range or Live tail; search request ID/internal event,
and compare recent deployment changes. Copy/export app message text for the CLI.
Do not assume provider HTTP logs have the same privacy rules or latency definition.
[Official log viewer](https://render.com/docs/logging),
[service metrics](https://render.com/docs/service-metrics).

During an active demo/release watch, the owner reviews Logs/health every minute
and runs the rolling summary on available exported messages. On a breach, inspect
the correlated ERROR, deployment SHA, mount and resource usage; use a non-destructive
recovery/rollback decision with the operator. Record symptom, time and resolution.
This is a manual watch process, **not a configured unattended alert service**.
#205/#208 must record a real service/dashboard URL, access/backup operator, retained
log/collection method and an actual notification channel/test if unattended
monitoring is required. No message is sent to a teammate by this code.

Render documents log retention by workspace plan and a per-instance ingestion
limit; verify the active plan/limits at provisioning. Platform resource graphs
are supplemental; use the documented request-event calculation for these
thresholds, and treat log gaps as missing evidence. Configure `/health` as the
host's HTTP health check when #205 provisions the service.
[Health-check setup](https://render.com/docs/health-checks).

## Evidence and pending release checks

2026-11-15 local Windows / Python 3.12.6 / pytest 9.0.2:

```text
python -m pytest -q tests/test_monitoring.py tests/test_backend_runtime.py tests/test_database_integrity.py
56 passed in 8.52s
```

The new 13 parameter variants cover three unusable-DB states/recovery, controlled
durations and non-disclosure/correlation, API+HTML database errors, unsafe method
normalization, sample/threshold boundaries, nearest-rank/window/de-duplication
and invalid-data handling. Existing healthy/missing/empty/corrupt tests are reused.
The #189 tests are reconciled with #223's actual FK-ON/503 contract; Windows path
and backup assertions match the already-prepared #205 correction without importing
its deployment infrastructure. No failing test is skipped.

[Synthetic CLI output](evidence/206/synthetic-metrics.json): 20 generated requests,
one 503, 5% error rate, p95 950ms and expected exit 2 at an explicit fixed timestamp.
This demonstrates arithmetic/CLI behavior only. Two pre-existing `src/app.py`
lint findings (SIM114 and UP017) also reproduce on main; changed imports are
formatted and the runtime/tool/test files pass Ruff. No public uptime, latency,
alert delivery or production-database failure rehearsal is claimed.

Release gate: verify actual HTTPS `/health`, a service-specific log/metrics view,
owner access and the manual watch process with real sanitized observations after
#205. Record the URL/SHA/time/results here and obtain independent teammate review
before considering the full #206 acceptance evidence complete.

Final full suite: `python -m pytest -q --junitxml=junit.xml` with installed Chrome
selected via PLAYWRIGHT_CHROMIUM_EXECUTABLE -> **203 passed in 135.44s**, zero
failures/errors/skips (190 retained + 13 new variants). The local loopback HTTP
rehearsal recorded **200 -> 503 -> 200** against temporary schema-only SQLite,
without creating the missing DB: [actual local evidence](evidence/206/local-health.json).
It also reduced the real captured request events to one readiness failure and
zero interactive requests. UTC timestamps, request IDs and source hashes are
stored in that report; these observed local durations do not establish public
latency or deployment availability. The public /health and provider-view evidence
still require the real #205 service.
