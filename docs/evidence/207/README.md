# #207 CI and main-protection evidence

`ruleset-current.png` is an actual headless Chromium screenshot of the public
GitHub ruleset page, with additional approval settings expanded. It is not a
reconstruction. `ruleset-page.txt` is that page's visible text.

The current organization rules require one PR approval but do not yet require
named CI checks. Repository administrator access is unavailable to the current
actor; proposed JSON is not evidence of applied protection. Later run/evidence
records distinguish actual GitHub checks from simulations and pending live
provider deployment. No credentials are stored in this directory.

| Artifact | Actual provenance |
|---|---|
| `github-state.json` | Actor permissions, active organization rules and missing required checks; latest green main workflow/job timestamps; actual Sprint 5 PR metadata |
| `red-rehearsal.json` | Actual GitHub job results for separate, closed/unmerged PR #231 |
| `red-log-summary.json` | Downloaded GitHub log lines: sole intentional failure, 228 existing passing cases and failing gate reason |
| `pytest.txt`, `pytest.xml` | Green implementation full-suite local console/JUnit, 228 passed in 57.74s, no skips |

The GitHub screenshot is baseline evidence with one required approval and no
required-status-check rule. An administrator must apply the proposed additional
rules and retain a new screenshot/read-back before that acceptance is complete.
See [the detailed evidence](../../ci-production-gate.md) and
[administrator procedure](../../main-protection-admin.md).

`merge-pytest.txt` / `merge-pytest.xml` record integration with main `55e81b5`:
**257 passed in 76.11s**, zero failures/errors/skips (229 main + 28 CI/protection
cases). These are separate from the original 228-case local run and the
intentionally failing, closed rehearsal. No administrator action or reviewer
approval is inferred from the passing suite.
