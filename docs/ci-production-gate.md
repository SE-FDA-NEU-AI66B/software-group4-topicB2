# CI production gate and main protection — #207

**Subsequent main integration (`55e81b5`):** all **257 tests passed in 76.11s**,
zero failures/errors/skips, and whole-repository Ruff passed. Both conflicting
testing-documentation sections were preserved, including database, monitoring
and release-rehearsal evidence. See [the integrated console](evidence/207/merge-pytest.txt)
and [JUnit](evidence/207/merge-pytest.xml). The dated audit below remains
historical; this integration does not apply administrator settings or certify
a live deployment.

Parent #200; deployment interface #205 / PR #226; operations evidence #208.
Date: **2026-11-15, Asia/Ho_Chi_Minh**. Execution: OpenAI Codex under the user's
authorization, GitHub actor `lesyhuy2k6-gif`. Status: **code/test rehearsal
complete; administrator configuration and live release evidence pending**.
No independent approval, production release or protection change is invented.

## Pipeline and deployment contract

`.github/workflows/ci.yml` keeps dependency installation, Gunicorn config check,
managed Chromium setup, the entire pytest suite/coverage/JUnit, both existing
security scans and optional Node job. No tests are skipped to make CI green.
Python Ruff is now blocking. Nine existing lint findings were repaired with
equivalent condition/context-manager/UTC/import cleanup; all original business
test nodes remain. `requirements-dev.txt` adds PyYAML only for workflow contract
tests; existing test/browser dependencies are retained.

`CI gate` runs with `always()` after detection, Python, security and optional
Node. Detection/Python/security must each be `success`. Missing/skipped/cancelled
required results fail closed. If Node is detected it must succeed; otherwise
its expected result is skipped. A skipped optional stack never masks failure
of required jobs.

Production deploy now depends on that gate. It additionally requires a push
to `refs/heads/main`, `RENDER_DEPLOY_ENABLED=true`, the protected `production`
environment, current main SHA and the existing exact-SHA/provider/HTTPS-health
validation. `tools.deploy_render` refuses a missing/non-success `CI_GATE_RESULT`
before any provider call. A green PR does not itself deploy, bypass approval
or establish that the deployed service is healthy.

Workflow token permission remains **`contents: read`**. Provider credentials
exist only as `production` environment Secrets, never in tests, PR jobs, YAML
values, artifacts or command arguments. The deploy step receives
`RENDER_API_KEY` from Secrets and the service ID from Variables. The configured
Render Blueprint retains `autoDeployTrigger: off`; #205's checks reject competing
platform auto-deploy. No PR-target workflow or automatic self-merge is added.

## Real negative PR rehearsal

Separate [draft PR #231](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/231),
SHA `2c956e014113b5e18a20c19873703ba3b8b6472a`, adds one intentionally failing
test on `evidence/207-failing-ci` only. It was **closed without merge** after
collecting actual GitHub results; its test is absent from this implementation
branch. Existing 228 tests remained green.

| Actual PR-run check | Result / evidence |
|---|---|
| Full suite | [Python tests](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43733767041/job/132871781285): **1 failed, 228 passed in 34.17s**; sole failure `tests/test_intentional_ci_failure.py::test_intentional_failure_blocks_release` |
| Lint and security | Lint step success; both security scans success; no masking of the deliberate failure |
| Aggregate gate | [CI gate](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43733767041/job/132872061101): failure, `Required CI job did not succeed: PYTHON_RESULT` |
| Production deploy | [Deploy job](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43733767041/job/132872091198): skipped, no steps or provider request |

[Full job metadata](evidence/207/red-rehearsal.json) and
[actual log excerpts](evidence/207/red-log-summary.json) retain the result.
This proves that the deliberately red PR did not deploy and that the aggregate
gate actually rejected its failed suite. The PR/main-only guard independently
blocks PR deployment. It is **not** a red-main production experiment or proof
of a live provider rollout; no failing test was pushed to main.

## Latest observed green main and real duration

Main `6acf0dd42b0a8b56831deedc519c194b474a519c`:
[CI run 43731613604](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43731613604),
**success**. GitHub reports start **2026-11-15T15:45:07Z** and update/completion
**15:46:25Z**: **78 seconds** elapsed from `run_started_at` to `updated_at`,
including orchestration/queue overhead. This is workflow duration, not application
response time. [Snapshot/job timestamps](evidence/207/github-state.json) retain
the measured fields and step outcomes.

That main run precedes this PR's new gate. It is not substituted for a reviewed
merge of this change. At inspection, repository Variables were empty and no
`production` environment existed; deploy was skipped. A reviewed green merge
becomes eligible to release only after #205 configures the actual provider,
environment/Secrets/Variables and deployment opt-in. Existing positive fake-provider
tests verify exact tested-SHA submission/readiness, not a real hosting event.

## Current main rules: actual screenshot and access blocker

The active organization ruleset `main-protection` (ID 21540407) targets the default
branch, restricts deletion/force push and requires a PR with **one approving
review**. Active rules currently contain **no required-status-check rule**.
Do not infer no protection from the classic branch-protection endpoint's 404:
the organization ruleset is real and active.

[Actual GitHub ruleset screenshot](evidence/207/ruleset-current.png),
[visible page text](evidence/207/ruleset-page.txt), and
[live public rules page](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/rules/21540407)
show the existing configuration with approval settings expanded. This image
was captured from the real GitHub page, not rendered from our proposal. It does
**not** show required checks enabled.

GitHub reported actor permissions: `push=true`, `admin=false`, `maintain=false`.
The user was asked to arrange administrator access/application; no grant or
administrator action has yet been verified. A JSON file or local passing test
does not enable protection. The exact remaining configuration and application
steps are in [the administrator handoff](main-protection-admin.md).

Proposed supplemental repository ruleset `.github/main-protection.json` requires:
PR + one approval, stale-approval dismissal, approval of the most recent push,
no bypass actors, no force-push/deletion, and strict/up-to-date named checks
**`CI gate`**, **`Python tests`**, **`No secrets committed`** from GitHub Actions
(App ID **15368**, verified from actual check metadata). It does not edit or
remove the existing organization ruleset.

After an administrator applies it, re-read active rules, obtain a new screenshot
showing required checks, and verify blocked merge behavior. Those final settings
and screenshot are still pending. CI's informational “Someone else must review”
job is not a replacement for enforced branch rules or an actual teammate approval.

## Separately reviewable Sprint 5 work

| Task / PR | Actual author | State at audit |
|---|---|---|
| #203 / [#225](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/225) UI evidence | `tlduongducanh281-jpg` | Merged |
| #205 / [#226](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/226) deployment interface | `tlduongducanh281-jpg` | Merged |
| #206 / [#228](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/228) monitoring | `tlduongducanh281-jpg` | Open |
| #204 / [#229](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/229) database/recovery | `lesyhuy2k6-gif` | Open |
| #210 / [#230](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/230) P0 release verification | `tlduongducanh281-jpg` | Open |

There are at least four separate planned/reviewable Sprint 5 PRs. This register
does **not** claim four green merged PRs or that every teammate already satisfies
the individual merge/review/closed-issue requirement. #207 adds another focused
PR; missing member contributions and independent reviews remain visible under #200.

## Local verification and remaining acceptance

Windows NT 10.0.26200.0 / Python 3.11.9 / pytest 9.2.0 / PyYAML 6.0.3 /
Playwright 1.65.2 / installed Chrome 157.0.8103.51. Full branch execution:

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE='C:\Program Files\Google\Chrome\Application\chrome.exe'
& .venv/m4-env/Scripts/python.exe -m pytest -v --cov --cov-report=term-missing --junitxml=docs/evidence/207/pytest.xml
# 228 passed in 57.74s; zero failures/errors/skips
& .venv/m4-env/Scripts/python.exe -m ruff check .
# All checks passed!
```

[Console](evidence/207/pytest.txt) / [JUnit](evidence/207/pytest.xml) retain
all 200 baseline cases plus 28 new CI/protection cases. Focused gate/deploy run:
**38 passed in 0.32s**. Main test/security/deploy contracts are retained.

Remaining required evidence: administrator applies/re-reads strict named checks
and captures the updated settings; teammate independently reviews this PR;
reviewed green main merge is observed; #205 records an actual eligible provider
deployment and readiness verification. No self-merge, live release, access grant
or final #207 completion is claimed while these requirements remain pending.
