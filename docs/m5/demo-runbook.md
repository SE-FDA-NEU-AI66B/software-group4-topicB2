# M5 live demo: 12 minutes + 5 minutes Q&A

Status: **prepared, not team-rehearsed and not public-release verified**. #211;
owner/Sprint 5 SM: Khuất Đình Trung. Team number **04** is user-confirmed; student IDs still need a reliable source
before the final PDF. The supplied brief says **2026-11-13 00:00**; today is
2026-11-16 in Vietnam. No new deadline/late-submission permission is invented.

## Timed running order

These are proposed speaking responsibilities, not claims about who authored
any code. Each member must explain their own actual PR/code during Q&A.

| Clock | Speaker | Live action and evidence | Exit condition |
|---|---|---|---|
| 00:00–01:00 | Trung | Introduce student/lecturer personas, replacing scattered feedback collection with assigned evaluations; name US01, US02, US03, US04, US11. | Exactly 1 minute; show the verified public origin, not localhost. |
| 01:00–03:00 | Trung | Private browser: first page → student sign-in → assigned evaluation → answer required questions → review → submit → return/reload Completed. Compare the visible Sign out before/after screenshots from #203. | US01/02/03, saved record survives reload; do not reuse a consumed evaluation. |
| 03:00–04:00 | Đức Anh | Sign out/student, sign in/lecturer, choose assigned feedback; show count/ratings/comments and exclusion of drafts. Compare lecturer permission-error recovery screenshots from #203. | US04 is reachable by clicks. |
| 04:00–05:00 | Huy | Demonstrate the instructor-selected business rule using a prepared synthetic case (menu below). Screen must explain problem, reason and next action after a real server refusal. | Do not count client-only validation as proof of a server rejection. |
| 05:00–06:00 | Đức Anh | Use visible Sign out; reach login and show protected browser navigation requires sign-in. Point back to the persisted submission/lecturer evidence if asked. | US11; all five P0 demonstrated within this five-minute block. |
| 06:00–08:00 | Huy | Open actual main CI test step/count, then docs/testing.md at instructor-selected P0 normal/error/boundary mappings. Run the safe local mutation tool, show red at 24h equality, restored green and unchanged workspace hash. | Report actual current count; local mutation restored, never deployed. |
| 08:00–09:00 | Huy | Show green Actions, actual main protection/rules and HTTPS `/health`; explain reviewed merge → CI gate → exact-SHA deploy. | Use real current settings/dashboard, not only YAML. |
| 09:00–10:00 | Đức Anh | Show actual rollback action/evidence and defend SQLite + single-instance persistent storage versus PostgreSQL: simple relational setup now; change for concurrent scale/HA requirements. Link ADR in design.md. | Choice + alternative + change trigger; hosted rollback still needs rehearsal before claiming it. |
| 10:00–12:00 | Trung | One genuine lesson from operations.md, one known risk with owner/issue/plan, then conclude product demonstration. | Total 12 minutes; no fabricated lesson or completed risk mitigation. |
| 12:00–17:00 | All | Individual questions, anyone not yet heard, and one question from another team. Open the relevant member's real PR/source. | Each member can explain their own contribution in their own words. |

## Instructor-selected business-rule menu

- **Duplicate submission (preferred natural browser example):** open the same
  fresh evaluation in two tabs before submitting. Submit in tab A; in still-open
  tab B confirm the completed answers. The server rejects the second request;
  UI explains that it is already completed and links back. Verify only one saved
  response. Prepare only fake demo feedback. Do not reset a live DB to repeat it.
- **Deadline/closed/enrollment:** ask the data/deployment operator to prepare a
  disposable synthetic case and a safe action for the selected rule before the
  presentation. A form opened before expiry/closure can exercise the server's
  refusal. Do not modify real student records or a live shared evaluation ad hoc.
- **Required/rating/text limits:** show the UI constraint, and use the actual
  backend pytest mapping for server enforcement. A disabled browser button or
  client error alone is not proof of a rejected server write. If the instructor
  insists on a live refusal, coordinate the prepared case/operator action first;
  do not claim the UI sent an impossible value when it did not.

## Two before/after improvements: attribution gate

Use [docs/ui-improvements-m3.md](../ui-improvements-m3.md), not mock wireframes
presented as running-screen captures. Candidate 1 is visible student Sign out;
candidate 2 is actionable lecturer permission-error recovery. Their actual
before/after laptop/phone images are in [evidence/203](../evidence/203/).

**Still pending:** the original instructor/user M3 feedback establishing that
these specific changes were made in response to it. #203 explicitly records this
gap. Until that source is confirmed, call them verified UI improvements, not
verified feedback-attributable improvements. Released-UI comparisons also need
the public release/SHA. Do not silently mark this acceptance item done.

## Test demonstration and safe mutation

Observed green main `7c0b06e` ran **257 tests in 52.30s** (snapshot in
[evidence/211/readiness.json](../evidence/211/readiness.json)); that is a dated
observation, not the count to memorize. Refresh the main Actions link and actual
collected/pass totals immediately before rehearsal/final PDF. Test-case IDs,
collected test items and story points are different counts.

Use the existing tool from a clean local checkout with dev dependencies:

```bash
python tools/rehearse_business_rule.py --revision origin/main --output /tmp/m5-live-mutation.json
```

It exports a temporary copy, runs the three US02 24-hour boundary variants,
changes `<` to `<=`, observes the equality case turn red, restores the copy and
reruns green. The tracked source hash is checked unchanged. Budget the measured
local time and preinstall dependencies; never modify/deploy the public app for
this demonstration. If the tool cannot locate the unique expression or a case
fails unexpectedly, stop and explain the actual result rather than skip it.

| Instructor picks | Normal / error / boundary to find in testing.md |
|---|---|
| US01 | Valid demo-role login; wrong/unknown credentials; empty required credential. Do not invent a password-length limit. |
| US02 | Assigned retrieval; anonymous/wrong enrollment; 86399/86400/86401 seconds and expiry -1/0/+1 second. |
| US03 | Persisted submission; duplicate/required/closed; rating 0/1/5/6 and text 1999/2000/2001 where mapped. Five required answers is an example, not a maximum. |
| US04 | Assigned submitted feedback/count; unassigned/wrong-role denial; 19/20/21 submitted responses are count examples, not an access threshold. |
| US11 | Current-session logout/denial; repeated anonymous logout. Copied-cookie revocation remains the #216 decision, not a passing guarantee. |

## Five-minute Q&A preparation

- **Trung:** click paths and persistence; which rule is enforced on the server;
  where session controls/API responses live; actual PRs #218/#219 and test PR #221.
- **Đức Anh:** login/submission/ownership checks; transaction behavior; exact-SHA
  deployment, health/logs, and what evidence establishes a public rollout. Use
  their actual authored/reviewed PRs from the contribution ledger.
- **Huy:** isolated SQLite fixtures, constraints/backup/restore, CI gate and branch
  protection. Distinguish a local rehearsal, passing CI and a deployed result.
- **Any member not heard:** open their own code/PR and explain trigger → backend
  rule/data change → UI outcome → test → known limitation. Do not memorize a
  teammate's authorship claim.
- **Prepare for another team:** “What happens to SQLite data on redeploy?” Answer
  with the actual plan/mount and real restart evidence; if not verified, say so.
- **Ask another team:** “How do you prove the code at your public URL is exactly
  the reviewed/tested commit, and how do you recover both code and data?”

## Rehearsal log (not completed)

Record date, participants, public URL/deployed SHA, each segment's actual elapsed
seconds, actual CI count/link, business rule/result, M3 source links, mutation
artifact, health/protection/rollback evidence, Q&A gaps and next owner/action.
Do not fill successful timings or all-member attendance until a real team rehearsal.
