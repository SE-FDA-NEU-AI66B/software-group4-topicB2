# M4 clean-clone and independent review audit — #190

Audit date: **2026-11-15, Asia/Ho_Chi_Minh**. Execution operator: **OpenAI Codex
in the user's Windows workspace**, authenticated GitHub actor `lesyhuy2k6-gif`.
This is AI-assisted execution, not a claim that a teammate independently ran
the setup. Status: **evidence prepared; M4 sign-off remains blocked**.

## Scope and dependencies

[#190](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/190)
follows closed #170/#171; their historical closures are preserved. Refinement
#163 and documentation #164 define the scope. US01 #14 / #165, US02 #18 / #166 / #187,
US03 #22 / #167 / #184, US04 #50 / #168 / #185, and US11 #183 / #169 / #186
own the story mappings. Cross-story contract #188 and database audit #189 are
included. Backend PR #223 is a later integration dependency: its runtime changes
supersede several historical assumptions in #189.

## Fresh clone and environment

Source: `https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2.git`.
The fresh network clone resolved to **686bd9e5bdcbf03947b28cbf8afe393dd087792a**;
`git status --porcelain` was empty before testing. Clone and virtual environment
were separate directories under ignored `.venv/`; the environment was newly
created with `venv`, without system-site-packages. No database initializer,
manual application server, or production database was used. After execution,
`data/edusurvey.db` did not exist in the clone.

Environment: Windows NT **10.0.26200.0**, CPython **3.11.9**, pytest **9.2.0**,
Flask **3.1.2**, Playwright **1.65.2**, installed Chrome **157.0.8103.51**.
This validates Python 3.11 on this machine, not the CI Python 3.12 environment
or a second teammate's machine. Exact resolved packages are retained in
[requirements-resolved.txt](evidence/190/requirements-resolved.txt).

Executed PowerShell commands from `D:\software-group4-topicB2`:

```powershell
git clone https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2.git .venv/m4-clean-clone
& 'C:\Users\ADMIN\AppData\Local\Programs\Python\Python311\python.exe' -m venv .venv/m4-env
Set-Location .venv/m4-clean-clone
& '..\m4-env\Scripts\python.exe' -m pip install -r requirements-dev.txt
$env:PATH = 'D:\software-group4-topicB2\.venv\m4-env\Scripts;' + $env:PATH
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
python -m pytest -v --junitxml=junit.xml *> ..\m4-pytest.log
$testExit = $LASTEXITCODE
```

Installation exited **0**; `python -m pip check` subsequently returned
**No broken requirements found.** The optional browser executable override
uses existing Chrome; no managed Chromium download is claimed. Browser fixtures
start their own loopback server on an ephemeral port and stop it automatically.
API/rendering cases use Flask's test client. Shared API fixtures use temporary
SQLite and fixed application time; database rollback tests also override SQL
time. Some legacy fixtures still use live timestamps; repository-wide time
determinism is not claimed (see DB-189-F02 in testing.md).

## Actual result and blockers

JUnit start: **2026-11-15T22:14:44.225559+07:00**. Console result:
**5 failed, 185 passed in 53.22s**, exit **1**, **0 skipped, 0 errors**, 190 collected.
This duration measures suite execution, not application response time.
[Full console output](evidence/190/pytest.txt), [JUnit](evidence/190/pytest.xml),
and [all collected nodes/results](evidence/190/nodes.json) preserve the run.

| Failing real node | Observed failure / dependency | Required follow-up |
|---|---|---|
| `tests/test_backend_runtime.py::test_production_config_requires_explicit_secrets_and_storage[ssssssssssssssssssssssssssssssssssssssss-/data/app.db-True]` | #223 / BE-05: `/data/app.db` is not an absolute Windows path; runtime correctly rejects it | Runtime test owner: use an OS-native absolute path while retaining invalid-path checks |
| `tests/test_backend_runtime.py::test_online_backup_and_restore_round_trip` | #223 / BE-07: POSIX mode-bit assertion fails on Windows before round-trip assertions execute | Runtime test owner: verify Windows protection appropriately and retain backup/restore/no-overwrite checks |
| `tests/test_database_integrity.py::test_runtime_foreign_keys_finding` | #189 / DB-189-F01: expects FK=0; actual runtime FK=1 after #223 | Database/runtime owners: replace obsolete diagnostic with enforcement checks, preserving orphan rejection |
| `tests/test_database_integrity.py::test_submission_write_failure_rolls_back[new]` | #189 / DB-189-07: test connection asserts FK=0; backend returns sanitized 500 instead of propagating that assertion | Database/runtime owners: align FK/error contract and retain exact rollback/retry verification |
| `tests/test_database_integrity.py::test_submission_write_failure_rolls_back[draft]` | #189 / DB-189-08: same integration conflict; injected SQL failure is not reached | Same; retain exact draft snapshot and retry coverage |

No test was removed, skipped, xfailed or weakened for this documentation task.
The historical #189 green run remains historical. Its FK-OFF diagnostic is
**superseded**, not proof of a current production defect. New failing evidence
must be resolved and the complete suite rerun before sign-off.

## Traceability reconciliation

The 97 Section 3 rows in [testing.md](testing.md) were compared with the actual
JUnit nodes, including parametrized variants and unittest class components:
**97 mapped, 0 missing, all matched results passed**. See
[mapping-audit.json](evidence/190/mapping-audit.json). This checks node existence
and execution, not a fresh semantic review of every assertion. Additional audit,
runtime and browser nodes explain why 190 collected items exceed 97 case IDs.
The five failing nodes above are outside that 97-row story matrix.

The former 18 proposed mappings from refinement #163 are implemented by merged
PRs #220 (#184), #222 (#185), #221 (#186), and #213 (#187). #188 is closed via
#217; #189 is closed via #224, with subsequent integration failures recorded
above. Historical pending markers and dated runs are preserved as dated evidence;
they are not the current readiness status.

## Independent contribution and review evidence

The [GitHub audit snapshot](evidence/190/github-audit.json) records actual PR
authors, changed files, merge SHA/date, review bodies and commit IDs, inline
comments, issue states and CI job/step outcomes. Authorship below comes from PR
metadata and changed test files, never integrated test totals.

| Member | Merged automated-test contribution / closed issue | Independent substantive review | Actual CI evidence |
|---|---|---|---|
| `khuatnhatminhcfpro-cmyk` | [#182](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/182), `tests/test_student_evaluations.py`; [#166 closed](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/166) | [lesyhuy2k6-gif review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/182#pullrequestreview-5910287747): session clearing, duplicate-test integration and SQL scan/dependency concerns | [Run 43704430638](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43704430638): Python tests success; overall failure from secrets job |
| `tlduongducanh281-jpg` | [#172](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/172), `tests/test_submission_workflow.py` / `tests/test_submissions.py`; [#167 closed](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/167) | [lesyhuy2k6-gif review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/172#pullrequestreview-5910187908): persistence, failed-write consistency and deadline boundaries | [Run 43706013954](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43706013954): Python tests and overall CI success |
| `lesyhuy2k6-gif` | [#174](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/174), `tests/test_auth.py`; [#169 closed](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/169) | [khuatnhatminhcfpro-cmyk review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/174#pullrequestreview-5910168937): duplicate function, session clearing, lint and secrets checks | [Run 41796461263](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/41796461263): Python tests success; overall CI failure |

These reviews contain specific technical observations; approval alone is not
counted as substantive review. The reviews can precede later commits: this
audit does not certify re-review of every final merge SHA or independent local
re-execution. In particular, approvals on #191/#213/#217/#218/#219/#221 have
empty bodies and no retrieved inline comments. Their substantive-review evidence
remains **unresolved**. #220/#222/#224 have nonempty technical review bodies;
the snapshot retains the precise evidence and its limits. This PR itself still
requires independent teammate review.

Current baseline CI is explicitly red:
[main 686bd9e, run 43726596867](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43726596867),
[Python test job](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43726596867/job/132849801870).
Install and lint steps succeeded; Test failed. No exact Linux failure count is
claimed without its test log. Skipped Node jobs reflect no Node stack, not skipped pytest tests.

## Task states, Board and submission artifacts

GitHub REST re-read: **#163–#171 and #184–#189 closed; #183 and #190 open**.
The issue assignees changed since refinement (#186 now `khuatnhatminhcfpro-cmyk`,
#189 now `tlduongducanh281-jpg`, #183 now `khuatnhatminhcfpro-cmyk`).
[sprint4-board.csv](sprint4-board.csv) preserves the historical Board columns and
adds separately verified current issue state/assignee and current Board check.

The current [Project Board](https://github.com/orgs/SE-FDA-NEU-AI66B/projects/4)
GraphQL read returned **INSUFFICIENT_SCOPES** (`read:project` required).
No Board mutation or current status verification is claimed. A teammate with
Projects access must re-read Status, Testing Sprint/Priority, estimates and
assignees against current issue evidence; #190 must remain open until unresolved
requirements are satisfied. No closing keyword is used for this evidence PR.

[Screenshot](evidence/190/m4-evidence.png) and [PDF](evidence/190/m4-evidence.pdf)
are rendered summaries of the actual audit, clearly showing failures and pending
work. They are not GitHub UI screenshots, teammate reviews or release sign-off.
Their [HTML source](evidence/190/m4-evidence.html) links to the underlying evidence.

Task estimates remain **43 hours** in the historical refinement register
(26 original + 17 supplemental); **18 story points** belong to the five P0
stories. Neither figure proves completed velocity or actual effort. No meeting,
attendance, new sprint date, performance result or completion date is invented.

Remaining sign-off: fix/review the five failures and rerun the suite; verify
current PR CI; obtain missing substantive reviews and a separate human clean-clone
run; reconcile/re-read the live Board; then independently approve M4 submission.
