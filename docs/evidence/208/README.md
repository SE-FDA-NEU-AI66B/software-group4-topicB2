# #208 operations handover evidence and sign-off register

Client audit date: **2026-11-16**, Asia/Ho_Chi_Minh. Operator: OpenAI Codex,
authenticated repository actor `lesyhuy2k6-gif`. This is AI-assisted repository
inspection, not an instructor clarification, independent review or live host
certification. No credentials, database files or personal application data are
included.

## Actual observations

| Artifact / source | What it establishes | What it does not establish |
|---|---|---|
| [handover-audit.json](handover-audit.json) | Main `9c5d55c` matches green workflow 43739534488; real timestamps and every job/step; 116-second elapsed time | A production deployment: Deploy was skipped |
| [main-rules.png](main-rules.png), [visible text](main-rules.txt), [capture metadata](main-rules-source.json) | Actual public GitHub ruleset page with approval options expanded; PR/one approval, no named-check rule | The proposed strict rules being enabled; actor remains non-admin |
| GitHub Variables/environments/deployments inspection in audit JSON | Those lists were empty at inspection | Absence of every possible external service; provider access is not connected/verified |
| [#206 local HTTP evidence](../206/local-health.json) | Temporary schema-only SQLite readiness 200 → 503 → 200, missing DB not created, correlated safe events | Public HTTPS health, production outage or platform notification delivery |
| [#204 CLI restore](../204/restore-check.json) | Actual isolated snapshot/restore, integrity/FK/full logical equality and recovered synthetic marker | Scheduled/remote backups or a production recovery drill |
| [#204 timing-failure/green reports](../204/README.md) | Real browser synchronization findings, retained failing evidence and subsequent complete green run | Measured public latency or physical-device verification |
| [#207 closed red PR #231](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/231), [job/log evidence](../207/red-log-summary.json) | One intentional failure blocked CI gate; Deploy skipped; PR not merged | A reviewed green main commit actually deploying through a live provider |

Elapsed time is GitHub `updated_at − run_started_at` (116 seconds), including
workflow orchestration/queue time. Security/detection/Python/gate durations
overlap and are not added. UTC 2026-11-15 17:09:47–17:11:43 is ICT 2026-11-16
00:09:47–00:11:43. Deploy and Node were skipped; pytest cases are not described
as skipped by that observation.

## Instructor clarification: unresolved, not an invented seventh section

Inspected issue bodies and all available comments for #200/#204/#205/#206/#207/
#208/#210; each had zero comments at inspection. The task/parent briefs require
written clarification but supply no answer. No instructor statement was found
in these connected repository sources.

The user has been asked for the actual instructor reply/link and actual public
HTTPS URL; no answer has been received at this audit. The current operations
document preserves exactly the six enumerated sections as a **pending draft
interpretation**, not a confirmed amendment to the brief.

| Clarification field | Current record / completion requirement |
|---|---|
| Instructor identity/source | Pending named instructor and course/email/LMS source link or supplied reply |
| Question | Does the enumerated six-section list define the required structure, or was a specific seventh section omitted? |
| Exact answer and date | Pending; do not infer agreement from issue closure or passing CI |
| Responsible follow-up | @khuatnhatminhcfpro-cmyk as #200 coordinator/instructor liaison; @lesyhuy2k6-gif retains the answer in #208 |
| Compliance | Not claimed until the actual clarification is retained and any required change reviewed |

This register is supporting evidence outside operations.md, not a seventh
required operations section.

## Remaining acceptance and review

| Requirement | State / evidence to obtain | Responsible member |
|---|---|---|
| Public URL/platform and deployed SHA | No verified URL/service access; connect actual provider or provide URL, then record HTTPS health and P0 flows | @tlduongducanh281-jpg, #205/#200 |
| Hosted rollback | Record actual source/target deploy SHAs, schema/backup compatibility, action and post-rollback checks | @tlduongducanh281-jpg, #205/#210 |
| Current log/metrics dashboard and deterioration response | Record actual service link/access, sanitized observations, operator watch; test delivery before claiming unattended alerts | @tlduongducanh281-jpg, #206/#200 |
| Required named-check protection | Administrator applies/re-reads strict Actions checks and captures new settings; current screenshot only shows existing rules | Administrator + @lesyhuy2k6-gif, #207/#200 |
| Backups and archive | Record real off-host archive/access, secure transfer, schedule execution and hosted restore | @lesyhuy2k6-gif, #204/#208 |
| Instructor format/retention clarification | Retain exact reply/link; keep-online-until-grades date is also unconfirmed | @khuatnhatminhcfpro-cmyk, #200/#208 |
| Independent approval | New #208 PR needs teammate approval recorded with Review changes | Requested from teammate; pending |
| Substantive recorded review comment | Reviewer should assess the deployment boundary, rollback/storage safety, monitoring arithmetic and missing evidence; plain issue discussion or approval-only click is insufficient | New #208 PR reviewer; pending |

Closed dependency issues and merged implementation PRs remain historically
closed. Their state is not used as proof of the outstanding external acceptance
items above. Keep #208 open until its requirements are actually satisfied;
no automatic self-merge or fabricated review is authorized.

## Document validation

[document-check.json](document-check.json) records exactly six ordered sections,
**312 whitespace-separated words outside tables** (including headings and inline
commands/links), six risk rows covering all five layers, five maintenance rows,
four evidence-based lessons, 25 checked local links and preservation of the full
historical monitoring body. Structure passed; **final sign-off is false**.

The prose limit is reproducible without installing additional packages:

```python
from pathlib import Path
text = Path("docs/operations.md").read_text(encoding="utf-8")
prose = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("|"))
print(len(prose.split()))  # 312; includes headings and code, excludes table rows
```

The edit changes documentation only. No application/CI implementation or tests
were changed; no new unit tests were added for prose. GitHub's existing full CI
must still pass for this PR. Counts/links/metadata and `git diff --check` were
validated locally; no new public-health or production-rollback result is claimed.

## Follow-up after PR #233 merge — 2026-11-16

[PR #233](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/233)
was merged on November 15. The document is implemented; Board Todo was stale.
[Independent approval](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/233#pullrequestreview-5912048627)
by @tlduongducanh281-jpg is recorded. His
[substantive PR comment](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/233#issuecomment-6898760593)
distinguishes local restore from hosted rollback, and green CI from enforced
protection; it asks for owners and evidence for unresolved items. The register
above already assigns those owners and specifies the required records. This
meets the literal #208 approval plus substantive recorded-comment requirement;
the comment is ordinary PR discussion, **not** substantive Review changes
feedback for #212. Earlier pending-review rows above are historical and superseded
by this observation. No teammate review is created or impersonated here.

[Follow-up API evidence](followup-audit.json) pins main b26dfc8 to successful CI
43804267947: 118 seconds from 04:28:05 to 04:30:03 UTC (11:28:05–11:30:03 ICT).
Every job/step is retained. Deploy is skipped, so this is not a public release.
The original screenshot remains historical; current effective rules still lack
required named checks. Public URL, hosted logs/health/rollback, off-host storage,
keep-online date and instructor section-count clarification remain pending.
Keep #208 open and In Review while resolving these acceptance items.

The follow-up changes documentation/evidence only. Local checks revalidate the
six headings, <=800 prose words, risk/maintenance/lesson minima and local links;
CI runs the existing test suite. AI assistance: Codex — documentation verification.
