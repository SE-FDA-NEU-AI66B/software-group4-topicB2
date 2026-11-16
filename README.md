# EduSurvey — M5 demo access

[![CI](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/workflows/ci.yml/badge.svg?branch=main&event=push)](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/workflows/ci.yml?query=branch%3Amain+event%3Apush)

**Public HTTPS entry point: not yet verified.** No running application URL was
found in connected repository/deployment metadata. #205/#209 must supply and
verify it before this README can be a final public-demo entry point. No guessed
host or localhost address is presented as the released application.

[Current M5 deployment readiness and manual setup](docs/audit/m5-deployment-readiness.md) ·
[Pending live verification ledger](docs/audit/m5-live-verification.md).

EduSurvey collects university course evaluations and lets assigned lecturers
review submitted feedback. The instructions below describe the implemented UI.
Public testers will need only the verified URL and a private browser, not an install.

## Disposable demo accounts

These are **public synthetic seed credentials**, not real university accounts
or infrastructure secrets. They match the canonical seed and are checked locally;
their availability on an actual deployment is still unverified.

| Role | Email | Demo password | After Sign in |
|---|---|---|---|
| Student | `student1@edusurvey.edu` | `Password123!` | My Evaluations |
| Lecturer | `lecturer1@edusurvey.edu` | `Password123!` | Student Feedback Review |
| Administrator | `admin@edusurvey.edu` | `Password123!` | My account; administrator CRUD is outside this P0 release |

Use fake feedback only. Shared accounts share saved responses: a submitted
evaluation stays Completed and cannot be submitted twice. If every assigned
evaluation is completed/closed, ask the operator for a fresh synthetic evaluation;
**do not reset a live database**. Never reuse this demo password elsewhere.

## Five P0 stories — click from the first page

Until the real public origin is verified, these links open README walkthroughs;
the route column describes app pages, not GitHub-relative application links.
Final publication must add tested absolute UI links using that actual origin.

| Story | Click path in the application | App page | Walkthrough |
|---|---|---|---|
| US01 Sign in | First page → Try a demo account → enter credentials → Sign in | `/` or `/login` | [Sign in](#us01-sign-in) |
| US02 View evaluations | Student sign-in → My Evaluations → search/status filters | `/evaluations` | [Find work](#us02-view-evaluations) |
| US03 Submit evaluation | Active/Due soon card → Start evaluation → Review answers → Submit evaluation | `/evaluations/<id>/complete` | [Submit and reload](#us03-submit-and-reload) |
| US04 Review feedback | Lecturer sign-in → assigned evaluation → Review feedback | `/lecturer/feedback` → selected evaluation | [Review feedback](#us04-review-feedback) |
| US11 Sign out | Account controls → Sign out → Login | Visible Sign out button on authenticated pages | [Sign out](#us11-sign-out) |

## Team

| Member | GitHub |
|---|---|
| Le Sy Huy | [@lesyhuy2k6-gif](https://github.com/lesyhuy2k6-gif) |
| Khuat Dinh Trung | [@khuatnhatminhcfpro-cmyk](https://github.com/khuatnhatminhcfpro-cmyk) |
| Duong Duc Anh | [@tlduongducanh281-jpg](https://github.com/tlduongducanh281-jpg) |

Sprint 5 Scrum Master: **Khuat Dinh Trung (@khuatnhatminhcfpro-cmyk)**.

## Private-browser walkthrough

### US01 Sign in

Once the actual public link is published, open it in a new private/incognito
window. The first page is Login. Expand **Try a demo account** if needed, enter
the student email/password above, and click **Sign in**. Expect **My Evaluations**.
A lecturer reaches **Student Feedback Review**; an administrator reaches
**My account**. If credentials fail, contact the demo operator; do not try real
university passwords.

### US02 View evaluations

On My Evaluations, use search and the status filter. An Active/Due soon card
offers **Start evaluation**. Completed/Closed cards cannot be newly submitted.
The canonical fresh M5 seed leaves the Software Engineering evaluation available
to student1, while other completed feedback is already present.

### US03 Submit and reload

Click **Start evaluation** on an available card. Wait for the questions, choose
a rating for every required question and optionally enter a synthetic comment.
Click **Review answers**, then **Submit evaluation**. Expect the success message.
Reload: completion must remain. Use **Back to My Evaluations** to see Completed.
This writes shared demo data; a reload/restart is not permission to submit again.

### US04 Review feedback

Click **Sign out**, then sign in as the lecturer. The assigned-evaluation list
already contains submitted seed feedback. Click **Review feedback** for an
assigned evaluation to see completed counts, ratings and comments. The Software
Engineering evaluation includes the new student submission after the previous
step. Draft answers are excluded. Use **All evaluations** to return; no API client
or developer tools are needed.

### US11 Sign out

Click the visible **Sign out** button in the account controls. Expect Login;
protected pages must require sign-in again. Sign out between roles and close
the private window afterward. Administrator sign-in can be checked through
**My account**; it does not demonstrate unimplemented administrator management UI.

## Storage, availability and safe retries

The repository proposes **paid Render with a persistent disk** and one app
instance; actual platform/plan/mount and public cold-start behavior are not yet
verified. Only files under the confirmed mount are durable. The database setting
is `EDUSURVEY_DATABASE=/var/data/edusurvey.db`; a path alone proves no durability.

If the operator instead uses Render Free, its documented idle spin-down occurs
after 15 minutes, waking takes about a minute, and local SQLite is lost on
restart/redeploy/spin-down. Free cannot attach a persistent disk. This is a
conditional platform limitation, **not the confirmed deployment mode or a
measured delay for EduSurvey**. [Official Free limits](https://render.com/docs/free),
[persistent disk terms](https://render.com/docs/disks).

Production startup preserves existing data and refuses to silently reseed a
previously provisioned missing database. New `--m5-demo` data has open deadlines
seven days after first initialization; restarting does not extend them. Existing
files are never reset by the initializer. Contact the operator for unavailable
accounts, expired work or outages. [Storage/backup runbook](docs/database-operations.md).

## Optional local development — not the public deployment

Public testers should not need these steps. For contributors, see
[the complete setup guide](docs/SETUP.md). From a cloned checkout and activated
virtual environment:

Use a development shell without production settings, not the hosted service.

```bash
python -m pip install -r requirements-dev.txt
python tools/run_student_demo.py
```

Open the **local address printed by that tool**. This disposable demo has the
same sample accounts, an available student evaluation and lecturer feedback.
Data survives browser reload during that process and is removed when it stops;
starting a new process starts a new disposable database. It never resets the
production database. Do not present its loopback URL as a public release link.

## Testing, evidence and handover

```bash
python -m playwright install chromium
python -m pytest -v
```

Linux browser setup may also require Playwright system dependencies; see
[setup](docs/SETUP.md). The CI badge above targets this repository's real
`ci.yml`, **main push** runs; it is not an uptime badge or approval evidence.
Production releases require the full CI/security gate; required named-check
protection needs verified administrator configuration, not just a green badge.

| Reference | Purpose |
|---|---|
| [README access evidence](docs/evidence/209/README.md) | Actual local private-context walkthrough, account checks, badge/link audit and outstanding public verification |
| [P0 student UI](docs/p0-student-navigation.md) / [lecturer UI](docs/p0-lecturer-feedback.md) | Implemented routes, screenshots and earlier verification scope |
| [Backend map](docs/backend.md) / [runtime](docs/backend-runtime.md) | Server routes, environment and readiness behavior |
| [Deployment](docs/deployment.md) / [CI gate](docs/ci-production-gate.md) | Main-only green releases, rollback and protection evidence |
| [Operations](docs/operations.md) / [monitoring](docs/monitoring.md) / [database](docs/database-operations.md) | Health/logs/monitoring and backup/recovery policy; live-provider evidence remains required |
| [Sprint Board](https://github.com/orgs/SE-FDA-NEU-AI66B/projects/4/views/1) | Team planning; merged code does not by itself certify a hosted release |

The Definition of Done requires satisfied acceptance, green checks, independent
review/approval and verified evidence. [#209](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/209)
must remain open until the actual running HTTPS URL is the first line, absolute
UI links work, and a fresh private-browser tester verifies the deployed accounts
and all P0 flows. No placeholder URL or local-only result substitutes for that.
