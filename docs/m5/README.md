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

## Verification register — #211

This is preparation evidence, not a final v1.0/public demo/LMS submission. Team 04
is user-confirmed; existing repo names are retained, but no reliable student IDs
were found in the searched repo/history/M1 task/PDF sources. See
[team source audit](../evidence/211/team-sources.json).

| ID | Node in `tests/test_m5_submission.py` | Expected and actual check |
|---|---|---|
| M5-DOC01 | `test_committed_pending_data_refuses_final` | Current incomplete metadata only renders a marked draft; final mode raises. |
| M5-DOC02 | `test_incomplete_final_is_rejected` (9 variants) | Missing team, mismatched SHA, local/private/invalid URL, missing release/late arrangement/confirmations blocks final. |
| M5-DOC03 | `test_formatter_escapes_text_and_uses_supplied_metadata` | Synthetic formatter fixture emits escaped text, not injected script. It is not a real released team/app. |
| M5-DOC04 | `test_placeholder_or_duplicate_student_ids_are_rejected` (2 variants) | Placeholder or duplicate IDs cannot pass by merely checking confirmations. |

Actual local command `python -m pytest -q tests/test_m5_submission.py` →
**13 passed in 0.02s**. `ruff check .` and `git diff --check` pass. The draft PDF
was printed with real Chrome through Playwright, rendered for visual inspection
and text-extracted: **one page**, first line Running app: PENDING, Team 04,
correct Vietnamese names, three explicitly pending student IDs. Three existing
repository/CI/README links returned HTTP 200. CLI `--final` exited **2** and no
`Team04_M5.pdf` was created; [document-check.json](../evidence/211/document-check.json)
records the exact draft hash and scope. The formatter checks supplied metadata,
not the truth of human/provider attestations, and never publishes/uploads.

Safe mutation rehearsal on main `7c0b06e` used the existing temporary-export tool:
**3 baseline passed → 1 equality variant failed / 2 passed → 3 restored passed**;
workspace source unchanged. [Actual stage output/hashes](../evidence/211/mutation.json).
The latest observed green main CI ran **257 passed in 52.30s**; it is a dated
main observation, not the prep-branch test count or browser performance evidence.

The [readiness/contribution/rules sources](../evidence/211/README.md) explicitly
retain public-origin/deployed-SHA/release, official student-ID, M3 attribution,
team rehearsal, late-submission and final per-person evidence gaps. No successful
public tour, copied-cookie revocation, tag/release or course submission is claimed.

Latest deployment preparation: [M5 readiness audit](../audit/m5-deployment-readiness.md)
and [live verification ledger](../audit/m5-live-verification.md). These do not
turn the existing draft into a final release/PDF or a submitted document.
