# Backend runtime handover (local evidence; platform configuration pending)

The #204 [database runbook](database-operations.md) supersedes the earlier
initializer/backup details below: initialization now refuses an existing file
in every environment, builds privately and publishes without overwriting;
backups also validate foreign keys. It records the paid Render disk decision,
assigned backup policy and isolated recovery verification, with host deployment
checks explicitly pending. POSIX backup files use owner-only creation mode;
Windows ACL protection needs operator configuration and is not inferred from
POSIX mode bits.

This supplements the backend portion of #204/#205/#206/#208; it does not certify a public deployment or replace the final reviewed operations handover. No real production URL, platform dashboard, storage mount or alert channel has been verified.

## Run and provision

Install `requirements-prod.txt` on the hosting build. Run `gunicorn --config gunicorn.conf.py src.app:app` (the Procfile uses this command). The Linux host/proxy must supply HTTPS and a persistent writable volume. Use one application instance / one worker with four threads for this SQLite design. Do not use a free ephemeral filesystem as durable storage. The Flask development server and `tools/run_student_demo.py` are local tools, not the production server.

Configure these through the hosting environment, never commit their values:

| Variable | Value / meaning |
|---|---|
| `EDUSURVEY_ENV` | `production`; enables mandatory secret/path guards and Secure cookies. |
| `EDUSURVEY_SECRET_KEY` | A stable, randomly generated secret, at least 32 characters. Generate privately, e.g. `python -c 'import secrets; print(secrets.token_hex(32))'`; put it in the host's secret settings. Changing it invalidates existing signed sessions. |
| `EDUSURVEY_DATABASE` | Absolute database file path on the persistent mount, e.g. `/var/lib/edusurvey/edusurvey.db`. The path itself does not prove that the host actually attached durable storage. |
| `PORT` | Port supplied by the host; default 8000 for local WSGI checks. |

For a NEW empty demo deployment only, with the same production environment/path configured, run `python -m src.init_db --m5-demo` once, then start Gunicorn. This seeds the documented synthetic accounts, upcoming open deadlines, a fresh student submission slot and existing lecturer feedback. It does not reset deadlines on every restart. The initializer refuses an existing production DB; use reviewed migrations for later schema changes. Never run the original destructive development initializer against existing user data.

Verify the actual HTTPS homepage, `/health`, private-browser student and lecturer flows, persisted submission after reload/restart/redeploy, and non-disclosure on denial. Capture deployed commit from the hosting provider and compare it to the eventual v1.0 tag. Code changes alone do not verify storage durability, deployed SHA, or a ≤3,000ms browser outcome.

## Health and telemetry

`GET /health` performs real read-only schema and SQLite integrity checks. Good DB → 200; missing/empty/corrupt DB → sanitized 503, without creating a replacement file or returning a path/exception/credentials. No-store prevents a cached green probe. This is a read-readiness check, not a write-throughput/capacity guarantee.

The app writes JSON `request_completed` events to stderr with endpoint name, method, HTTP status and monotonic server duration in milliseconds. Unknown paths are named `unmatched`; actual path parameters/query strings, credentials, answers, cookies, tokens, IPs and account identities are omitted. Database failures use a generic event; unexpected failures include only endpoint and exception class. Production Werkzeug/Gunicorn raw access logs are disabled. Read these events in the selected host's application-log viewer or collected stderr stream; #205/#206 must record its real dashboard URL/access procedure once chosen. Dependency/host logging must be reviewed separately; do not enable raw request dumps.

Proposed operator policy (not observed production results): inspect rolling five-minute windows, excluding `health`/`static` from interactive requests. Error rate = count(status≥500) / total requests ×100; alert at ≥5% with at least 20 requests. Server latency = p95 of `duration_ms` for the same requests; investigate p95>1,000ms for five minutes. These diagnostic thresholds reserve time for network/navigation and do not establish the inclusive 3,000ms action-to-visible-outcome criterion. A collector/dashboard, notification channel and on-call recipient are not configured by this code; #206/#208 must record their real platform setup. Locally, stderr can be inspected directly; JSON lines are sufficient for aggregation.

## Backup and recovery

Run `python tools/backup_database.py /absolute/live.db /private/backup-unique.db` before migrations/releases and at the schedule selected under #208. SQLite's online backup API takes a consistent snapshot, checks integrity, refuses overwrite, and creates the backup with owner-only permissions. The file contains private application data: keep it outside Git/public assets and move it to access-controlled off-host storage under the agreed retention policy. This helper does not configure backup scheduling, encryption or remote storage.

For a recovery drill, use a copy and isolated instance. Stop all writers; keep an additional copy of the current DB before replacement. Run `python tools/backup_database.py /private/backup.db /private/restored-check.db` to validate/copy the backup, confirm expected records and `PRAGMA foreign_key_check`, then have the operator replace the configured DB while the service is stopped, retaining mount ownership/permissions. Restart and verify `/health`, both roles, persisted records and a new test submission. The automated test restores into a temporary path and never overwrites the working DB. Do not interpret that drill as a production recovery rehearsal.

For application rollback, retain the previous successful deployment SHA and redeploy it through the green-gated pipeline. Restore data only if needed and after checking schema compatibility/data-loss implications; an old app release does not automatically undo a schema/data change. #205/#207/#208 must supply the actual host-specific rollback action and evidence.

## Local verification

The audit exercised real Gunicorn 27.0.1 with `EDUSURVEY_ENV=production`, an ephemeral secret and a temporary seeded database. Observed: `/health` 200 → rename temporary DB away → 503 without replacement-file creation → restore DB → 200; HTML redirects to login; login sets Secure/HttpOnly/SameSite=Lax cookie; request logs omit supplied credentials. Local HTTP was used only for readiness/response-header checks; secure-cookie browser authentication on the real host still requires HTTPS. No production database was interrupted.
