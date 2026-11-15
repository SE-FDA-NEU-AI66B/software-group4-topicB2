# Production database, demo seed and recovery — #204

Parent: [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200).
Database owner: **@lesyhuy2k6-gif**; deployment owner: **@tlduongducanh281-jpg (#205)**;
release/operations evidence: **#207/#208**. This records an implemented and
locally tested storage contract, not a live hosting provision or teammate review.

## Storage decision and current hosting terms

Decision dated **2026-11-15**: keep SQLite on a **paid Render web service with
an attached persistent disk**, one instance, one Gunicorn worker/four threads.
This matches the proposed #205 environment/startup contract; this PR does not
purchase hosting, create a service or alter its deployment workflow.

Current official [Render disk terms](https://render.com/docs/disks) require a
paid service; only files beneath the disk mount persist. The disk is available
at runtime, not build/pre-deploy or separate one-off jobs. Disk-backed services
cannot scale to multiple instances and incur deployment downtime. Re-check
these terms before provisioning; account approval and the actual mount remain
#205 release checks.

[Render Free terms](https://render.com/docs/free) say local SQLite is lost on
restart, redeploy or idle spin-down; Free services cannot attach persistent
disks. **No ephemeral-disk durability or Free deployment is claimed.** Automatic
startup reseeding is not selected here. Changing to a course-permitted ephemeral
demo requires a separately reviewed mode with explicit data-loss disclosure in
README and operations. A path environment variable alone never proves durability.

### SQLite compatibility review

| Existing dependency | Decision / coverage |
|---|---|
| `src/app.py`: `sqlite3.Row`, `?` parameters, `lastrowid`, read/write URI, transaction contexts and per-connection FK pragma | Retain SQLite; existing API, persistence, rollback and isolation tests remain |
| `src/response_queries.sql`: named parameters and `ON CONFLICT ... DO UPDATE` | Existing UNIQUE constraints and schema retained; no PostgreSQL placeholder/UPSERT conversion |
| Reminder queries: SQLite `datetime(...)`, `INSERT OR IGNORE`; SQL/Python clocks | Retain current behavior; a database-engine migration would need separate query/timezone compatibility tests |
| `src/schema.sql`: nine tables, FKs/CHECKs/UNIQUEs and destructive DROP statements | Canonical schema is executed only on a private new database; never on existing application storage |
| `tools/backup_database.py`: SQLite online backup API | Consistent live snapshot with integrity/FK checks; source opened read-only, destination exclusive |

No schema change or second schema is needed for this task. Future migrations
must be reviewed incremental changes with a pre-migration backup, old/new app
compatibility tests and a restore/rollback plan. The seed file is not a migration.
SQLite is suitable for this single-instance course demo, not a claim of
multi-writer scalability; the existing timeout is five seconds.

## Environment and safe first initialization

| Setting | Target value / responsibility |
|---|---|
| `EDUSURVEY_ENV` | `production` |
| `EDUSURVEY_DATABASE` | `/var/data/edusurvey.db`, on the actual mounted disk |
| `EDUSURVEY_DATA_MOUNT` | `/var/data`, used by #205's startup guard |
| `EDUSURVEY_SECRET_KEY` | Stable private random value, at least 32 characters; host secret settings only |
| `EDUSURVEY_BOOTSTRAP_DEMO` | `1` only for explicit first synthetic-demo provisioning through #205's guard |
| `PORT` | Supplied by host; Gunicorn binds to `0.0.0.0` |

Runtime command for a **confirmed empty new mount** with that environment:

```bash
python -m src.init_db --m5-demo
python -m tools.verify_database /var/data/edusurvey.db
gunicorn --config gunicorn.conf.py src.app:app
```

Run initialization once, at runtime where the volume is attached. Do not put
the initializer unconditionally before Gunicorn: later attempts intentionally
refuse an existing file. #205's `tools.prepare_production` integration owns
idempotent startup verification and its provisioned marker. That deployment
implementation is now merged in main by PR #226; this PR validates
compatibility but does not claim live provisioning. Missing previously provisioned
data is a recovery event, not permission to reseed.

The initializer builds the canonical schema/seed in a private temporary file
beside the target, commits and validates FKs, then publishes using an exclusive
hard link. Existing, empty, corrupt or concurrently created target files are
never overwritten, in any environment. Seed failure cleans its temporary file
without publishing a partial target. Local filesystems must support hard links
(Render's local disk / Windows NTFS do); unsupported filesystems fail closed.
A process kill can leave a private temporary file: inspect and clean it only
after confirming no initializer is running. The initializer never silently
refreshes existing deadlines or resets user submissions.

## Synthetic first-screen data and accounts

`--m5-demo` creates six users, five courses, ten evaluations and thirty questions
from the existing seed. Open deadlines are set seven days after initialization;
student1/evaluation1 is intentionally unanswered. Assigned lecturer feedback
already includes submitted ratings/comments; draft responses are excluded.
The seven-day window expires normally; extending it requires a reviewed data
change, not a restart reset.

| Role | Synthetic login | Password | First screen |
|---|---|---|---|
| Student | `student1@edusurvey.edu` | `Password123!` | `/evaluations`: active work and existing completion history |
| Lecturer | `lecturer1@edusurvey.edu` | `Password123!` | `/lecturer/feedback`: assigned courses and nonempty submitted feedback |
| Administrator | `admin@edusurvey.edu` | `Password123!` | `/account`: role/account information; no administrator CRUD feature is claimed |

These are intentionally public synthetic demo credentials. Do not load real
student data into the public course demo. A browser submission is committed to
the configured SQLite file and survives reload; local tests also launch a new
application process and verify the committed record. Host restart/redeploy
survival still requires confirming the real disk, as described below.

## Backup policy and isolated restore procedure

The following is the assigned **operating policy**, not a claim that a remote
scheduler/archive already exists.

| Item | Owner / policy |
|---|---|
| Execution | @lesyhuy2k6-gif; deputy @tlduongducanh281-jpg while performing #205 releases |
| Frequency | Daily at 00:30 Asia/Ho_Chi_Minh, plus immediately before releases/migrations; manual execution/log until an approved scheduler exists |
| On-disk location | `/var/data/backups/edusurvey-<UTC-timestamp>.db`, private directory on the same durable mount; this is a staging copy, not disaster protection |
| Off-host location | Owner's access-controlled encrypted workstation archive, `~/EduSurveyBackups/`; owner must record the real machine/path and successful secure transfer in #208 before public release |
| Retention | Seven daily and four weekly copies; prune only after a newer copy has passed an isolated restore check; no automatic deletion is implemented |
| Verification | Integrity + FK check on each backup; restore drill before launch and weekly, recording date, SHA, expected records and result |
| Recovery limits | Daily schedule implies up to 24 hours of data loss if the latest off-host copy is current; no measured production recovery-time objective yet |

On the mounted service runtime shell (not a separate Render cron/one-off job):

```bash
umask 077
mkdir -p /var/data/backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
python tools/backup_database.py "$EDUSURVEY_DATABASE" "/var/data/backups/edusurvey-$stamp.db"
python -m tools.verify_database "/var/data/backups/edusurvey-$stamp.db"
```

The helper uses SQLite's online backup API, checks integrity/FKs on source and
copy, refuses an existing destination and removes only its own failed partial
output. POSIX creation mode is owner-only; Windows exposes read/write attributes
and requires separate ACL configuration. Backups contain account/answer data;
keep them out of Git, logs, public assets and deployment artifacts. Transfer
off-host securely; a copy on the same volume cannot survive loss of that volume.

Perform the drill in an isolated directory with no writers to the snapshot:

```bash
python tools/backup_database.py /private/snapshot.db /private/drill/restored.db
python -m tools.verify_database /private/snapshot.db --compare /private/drill/restored.db
```

Verification is read-only, never creates a missing file, checks all nine tables
and compares schema, sequence values and every row with the offline snapshot.
Only counts/status are printed, not hashes, credentials or answers. Do not compare
against a concurrently changing live source. The automated drill also changes
the original after backup, verifies those changes are absent in the restored
copy and uses Flask login/student completion/lecturer feedback on the restored DB.

For real recovery: stop the service and all writers; preserve the failed/current
file and related journals as incident evidence; restore into a new path first;
verify schema/app version compatibility and records; configure the service to
use the validated candidate on the persistent mount; restore ownership/permissions;
restart and verify health/login/feedback/submissions. Never overwrite a live
SQLite file or copy an active `.db` alone while WAL/journal writes may exist.
Record the data-loss interval and operator approval in #208. Provider disk
snapshots do not replace the application-level restore drill.

## Evidence and remaining host verification

[tests/test_production_database.py](../tests/test_production_database.py) uses
temporary canonical databases, fixed application time, real password verification,
Flask clients, a separate Python process and actual Chromium reload. The recovery
test creates/submits a record before backup and validates it through both roles
after restore. Failure injection verifies no partial initializer publication,
concurrent-winner preservation and backup-failure cleanup. No production storage
or database dump is used or committed. Results are mapped in [testing.md](testing.md).

Before #205/#208 claim deployment completion, record the actual service URL/plan,
mounted path and deployed SHA; log in as all three roles; create a submission,
reload, restart and redeploy; verify the same record and health after each step.
Record the off-host archive/transfer and a service-level restore drill. These
host actions are **pending**, not inferred from local tests or hosting terms.
An independent teammate must review this PR; no self-merge or review is claimed.
