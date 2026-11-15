# v1.0 release and submission gates — #211

Prepared checklist only. No tag, GitHub release or LMS upload has been created.
See [readiness snapshot](../evidence/211/readiness.json) for actual observations;
refresh every release-dependent fact before acting.

## Before tagging

- [ ] #211 prep PR is independently reviewed/merged; release code is reviewed.
- [ ] #203's two improvements have original M3 feedback attribution and released-UI proof.
- [ ] #209 has the actual HTTPS origin on README line one, deployed demo accounts,
      clickable UI starts and verified private-desktop/phone P0 walkthroughs.
- [ ] #210 records real public P0/persistence/error checks, current test counts,
      restored local mutation and health/rollback verification.
- [ ] #208 sign-off/platform contacts/runbook are real and current.
- [ ] Main CI gate is green for the candidate commit; actual protection requires
      PR + independent approval + green required check. Inspect real settings.
- [ ] Deployment operator records public origin, service/deploy ID and full live
      commit SHA from the provider, not a guessed main HEAD or health-only result.
- [ ] Read-only public homepage and `/health` are healthy; no deploy is racing
      the release. Freeze/recheck release identity with the operator.
- [ ] Full deployed SHA equals the reviewed/tested release candidate; the commit
      belongs to main. If deployment lags, wait/redeploy or release the actually
      deployed tested SHA — never tag a different main commit for convenience.
- [ ] Sprint 5 minimums have actual evidence: ≥4 reviewed green merged PRs; each
      member ≥1 merge, ≥1 recorded review and ≥1 closed issue; #212 wrap-up and
      five-sprint/velocity log are complete. Assignment alone proves none of these.
- [ ] Confirm official team number, spellings/student IDs, genuine late-submission
      arrangement and a 12+5 minute team rehearsal; do not invent dates/attendance.

## Exact-SHA tag and three-line release

These are **future operator commands**, not commands already executed. Only run
after every gate above is backed by real evidence. Set `M5_RELEASE_SHA` to the
provider-confirmed full SHA from the release ledger, not `git rev-parse main`.

```bash
set -euo pipefail
: "${M5_RELEASE_SHA:?Set the verified deployed 40-character SHA first}"
[[ "$M5_RELEASE_SHA" =~ ^[0-9a-f]{40}$ ]]
git fetch origin --tags
git merge-base --is-ancestor "$M5_RELEASE_SHA" origin/main
# Inspect the successful main CI run for this SHA and provider record before continuing.
git tag -a v1.0 "$M5_RELEASE_SHA" -m "EduSurvey v1.0"
git push origin refs/tags/v1.0
gh release create v1.0 --verify-tag --title 'EduSurvey v1.0' --notes-file docs/m5/v1.0-notes.txt
git rev-parse 'v1.0^{commit}'
gh release view v1.0 --json url,tagName,isDraft,isPrerelease
```

Stop if v1.0 already exists; resolve/verify it rather than force-retagging. An
annotated tag's object SHA differs from its commit SHA: compare the dereferenced
`v1.0^{commit}` to the provider commit. Recheck provider SHA and URL after publish.
Do not self-merge an outstanding PR or bypass branch protection to finish this.
The [notes file](v1.0-notes.txt) contains exactly three proposed summary lines;
it is not a claim that a release has already been published.

## Final PDF and course upload

1. Update [submission.json](submission.json) from confirmed information/evidence.
   `main_ci_url` must be the latest actual green main CI run, not the prep-branch
   CI. Keep a separate run proving the deployed release SHA if main has advanced.
2. Verify the literal public origin and `/health`, repository, published v1.0
   and CI links; run the README against the deployed seed. Record source URLs,
   full SHAs and time. Check the published release's tag commit equals live SHA.
3. Fill confirmations only after the actual checks, team rehearsal and instructor
   reply. The builder checks supplied metadata consistency/completeness; it does
   **not independently authenticate** provider records, links, human attendance
   or instructor permission. This checklist/evidence must supply that verification.
4. Run `python tools/build_m5_submission.py --final --pdf`. Correctly complete
   data produces **Team<NN>_M5.pdf**; the official brief uses this numbered filename.
   Current pending data refuses final mode. Inspect the final PDF's first line
   (`Running app: actual HTTPS URL`), accents/student IDs, all links and page breaks.
5. Upload only after the user explicitly authorizes the course submission and
   identifies the correct assignment. Record actual upload/receipt/time; creating
   a local PDF or GitHub release is not course submission. Never request/commit
   course passwords or provider secrets in the JSON/PR.

## Contribution/release ledger (pending confirmation)

| Member | Merged PR + green check | Review given | Issue closed | Actual merge action / source |
|---|---|---|---|---|
| Khuất Đình Trung | #218, #219, #223 | None found in declared merged-M5 subset; final audit needed | #201, #202, #214, #215 | Recorded merge actor on #218/#219/#223 |
| Dương Đức Anh | #225, #226, #228, #230 | #218, #219, #229, #232, #233 | #203, #205, #206, #210 | Recorded merge actor on #225/#226/#228/#230 |
| Lê Sỹ Huy | #229, #232, #233 | #223, #225, #226, #228, #230 | #204, #207 | Recorded merge actor on #229/#232/#233 |

[Contribution snapshot](../evidence/211/contributions.json) found **10 merged PRs
with successful recorded head checks and an independent approval** in the declared
M5 milestone/task-title subset. These are actual GitHub records, not assigned work.
Open/other eligible work is outside that subset and must be checked before a final
per-person conclusion. The source flags cases where merger equals author; do not
infer who physically operated GitHub or whether a course self-merge policy accepts
those actions. No automatic merge or compensating review was performed here.
Trung's recorded-review minimum is not established by this snapshot; #212 must
resolve the genuine evidence, not fabricate a review. Issue closure alone does
not prove the public/deployment acceptance of #203/#205/#206/#210.

Record public origin, provider service/deploy ID/full SHA, tag commit, release
URL, latest green main CI, tested candidate CI, health/status time, P0/rollback
proof, M3 feedback sources, rehearsal log, team confirmation and upload receipt.
The original due time is 2026-11-13 00:00; the current date is 2026-11-16 ICT.
Late-submission terms remain unconfirmed; no extension is inferred.
