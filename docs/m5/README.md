# M5 release/demo/submission preparation — #211

**Prepared, not finalized or submitted. Team 04 is user-confirmed.** No actual public origin, provider SHA,
v1.0 release, student IDs, original M3 feedback attribution,
completed team rehearsal or late-submission arrangement is confirmed by this
preparation. Dependencies are not considered satisfied merely because a PR merged.

- [12+5 minute demo and Q&A](demo-runbook.md): proposed speakers, click-through,
  instructor-rule menu, actual test/mutation references and attribution gaps.
- [Release/finalization checklist](release-checklist.md): exact deployed SHA/tag
  alignment, three-line release, genuine evidence and course-upload boundary.
- [Submission metadata](submission.json): fill only confirmed information.
- [Draft PDF](Team04_M5_DRAFT.pdf) / [HTML source](Team04_M5_DRAFT.html):
  visibly incomplete preview; not the required final Team<NN>_M5.pdf.
- [Team sources](../evidence/211/team-sources.json): Team 04 is user-confirmed; names match repo; MSSV not found in searched repository/history/PDF sources.
- [Contribution snapshot](../evidence/211/contributions.json): actual actors/reviews in the declared subset; final per-member acceptance remains open.
- [Readiness snapshot](../evidence/211/readiness.json): actual GitHub main CI and
  dependencies, empty deployment/release metadata and unresolved checks.
- [Fresh local mutation](../evidence/211/mutation.json): safe temporary-copy
  red/green/restored proof, not a public app change or an all-member rehearsal.

Rebuild draft (Playwright/dev dependencies and Chromium installed):

```bash
python tools/build_m5_submission.py --pdf
```

A local installed Chrome can be selected through `PLAYWRIGHT_CHROMIUM_EXECUTABLE`.
The draft PDF starts with Running app: **PENDING**, and is prominently marked
DRAFT/NOT READY. Final mode (`--final --pdf`) refuses today's incomplete data.
The formatter checks supplied values/acknowledgements; it does not establish the
truth of deployment/human/permission evidence and never tags/publishes/uploads.
Follow the release checklist before changing a confirmation to true.

The supplied deadline is 2026-11-13 00:00. Confirm the actual late-submission
arrangement with the instructor; no new deadline or submission is claimed here.
