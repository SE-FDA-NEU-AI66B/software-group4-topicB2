# Sprint 4 Backlog Refinement

Evidence date: **2026-11-15** (Asia/Ho_Chi_Minh). Refinement issue: [#163](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/163). Source: fetched `origin/main` **5a52af6**, requirements, current route/schema code, existing pytest collection, issues #163–#171 and merged PRs #172/#173/#178/#180/#181/#182. This is a current refinement snapshot, not a reconstruction of an earlier planning meeting.

## Scope and readiness

Sprint goal: make automated testing of all five P0 stories traceable, reproducible and ready for implementation/review, retaining verified baseline work and explicitly planning the remaining acceptance gaps.

The repository baseline runs **106 tests successfully** (`python -m pytest -v`: **106 passed in 2.95s**, Python 3.12.4 / pytest 7.4.4, macOS). This refinement changes documentation and GitHub backlog metadata only. It does not implement the new planned tests or change application rules.

**Board verified:** after the user authorized Projects access, all **21 issue items** were applied and re-read successfully on the [Sprint Board](https://github.com/orgs/SE-FDA-NEU-AI66B/projects/4/views/1). #163 is **In Review**, eight closed baseline tasks remain Done and all seven follow-ups are Todo. Assignees, milestones and native parent relationships match the issue records. This refinement is ready for independent review; #163 closes through the reviewed PR rather than an automatic self-merge.

Board-specific decisions preserve history: the four closed parent stories retain their original **Sprint 3** iteration, while testing tasks and restored US11 story #183 use the existing **Sprint 4** iteration. **Testing Sprint = Sprint 4** explicitly includes all five P0 stories and all 16 tasks in the testing scope. GitHub reports the native Priority field as derived from issue fields and rejects option edits, so **Testing Priority** stores P0/P1/P2 alongside the existing repository priority labels. **Estimated hours** stores task estimates separately; **Point** and **Points** are unchanged. No unrelated Board item was modified.

The real Sprint 4 iteration starts **2026-11-01**, lasts **13 days**, and is already listed as completed by GitHub. Its dates were preserved. The 2026-11-15 audit and remaining work are a late refinement snapshot, not evidence that future tests were finished within that earlier iteration.

## P0 stories and test strategy

[requirements.md](requirements.md) identifies exactly these P0 stories. Parent issues already closed remain closed; their historical completion is not a claim that every M4 acceptance example is automated. US11 had no dedicated story issue; [#183](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/183) restores it using the existing two-point requirement and preserves its known remaining gaps. The erroneous `#1` parent reference in #169 is corrected.

| Story | Parent | Test responsibility | Normal evidence | Error evidence | Boundaries / remaining work |
|---|---|---|---|---|---|
| US01 User Login and Authentication | [#14](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/14) | Khuat Dinh Trung | TC-01, US01-A01/A02: student/lecturer/admin demo login | TC-02/03/04: wrong password, unknown email, missing password; anonymous/role restrictions | No password-length limit is enforced, so none is invented. All three role values are tested. Exact wording and 3-second evidence: [#188](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/188). |
| US02 View Available Course Evaluations | [#18](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/18) | Khuat Dinh Trung | TC-05 and existing list/status cases | TC-06/07: anonymous/lecturer denied; enrollment isolation US02-L08 | TC-08/09/10 at 86399/86400/86401 seconds; TC-11/12/13 at expiry -1/0/+1 second already automated. Three-active-evaluation example US02-L12: [#187](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/187). |
| US03 Complete and Submit Course Evaluation | [#22](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/22) | Duong Duc Anh | TC-14 / TC-US03-01: response and answers persisted | TC-15/16/17 and TC-US03-02–06: missing answers, duplicate, unauthorized, invalid/closed/expired evaluation | Exact deadline boundaries implemented. Rating 0/1/2 and 4/5/6, trimmed text 1999/2000/2001, four/five answers to five required questions: [#184](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/184). |
| US04 Review Submitted Student Feedback | [#50](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/50) | Duong Duc Anh | TC-32, TC-US04-01/06/07: assigned-course data and submitted count | TC-33/34/35 and TC-US04-02/03/04: unassigned, wrong role, anonymous | TC-37 and TC-US04-08/09 plan counts 19/20/21 under [#185](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/185); 20 is an acceptance example, not a maximum. Drafts must remain excluded. |
| US11 User Sign Out | [#183](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/183) | Le Sy Huy | TC-US11-05/06 and TC-38: successful logout and session removal | TC-US11-07: subsequent protected access denied | TC-39/40/41 plan student/lecturer post-logout denial and two anonymous logout calls: [#186](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/186). No logout-count/time limit is invented. Redirect, copied-cookie and timing claims need [#188](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/188). |

Each story has at least three concrete normal/error cases in [testing.md](testing.md). The matrix now contains **97 unique cases: 79 existing mappings and 18 NOT IMPLEMENTED plans**. Case count differs from collected pytest items because some legacy IDs map to the same function. Existing IDs and mutation evidence are preserved; proposed functions are explicitly distinguished from real collected nodes.

## Prioritized task register

The following issue metadata, estimates and Board statuses were verified after writes on 2026-11-15. The Board uses existing Todo / In Progress / In Review / Done options and the real Sprint 4 iteration; no dates were invented. Cross-story tasks have explicit related issues instead of invalid `#0` parents.

| Issue | Work | Responsible member | Estimated hours | Parent | Priority | Repository state | Verified Board status |
|---|---|---|---:|---|---|---|---|
| [#163](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/163) | Refine Sprint 4 backlog | @khuatnhatminhcfpro-cmyk | 2 | Cross-story | P0 | OPEN | In Review |
| [#164](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/164) | M4 automated testing documentation | @khuatnhatminhcfpro-cmyk | 3 | Cross-story | P0 | CLOSED | Done |
| [#165](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/165) | US01 authentication tests | @khuatnhatminhcfpro-cmyk | 3 | [#14](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/14) | P0 | CLOSED | Done |
| [#166](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/166) | US02 evaluation-list tests | @khuatnhatminhcfpro-cmyk | 3 | [#18](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/18) | P0 | CLOSED | Done |
| [#167](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/167) | US03 submission tests | @tlduongducanh281-jpg | 4 | [#22](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/22) | P0 | CLOSED | Done |
| [#168](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/168) | US04 lecturer-feedback tests | @tlduongducanh281-jpg | 3 | [#50](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/50) | P0 | CLOSED | Done |
| [#169](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/169) | Shared fixtures, database and US11 baseline | @lesyhuy2k6-gif | 4 | [#183](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/183) | P0 | CLOSED | Done |
| [#170](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/170) | Automated testing setup guide | @lesyhuy2k6-gif | 2 | Cross-story | P0 | CLOSED | Done |
| [#171](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/171) | Sprint 4 wrap-up baseline | @lesyhuy2k6-gif | 2 | Cross-story | P0 | CLOSED | Done |
| [#184](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/184) | Complete US03 rating, text and required-answer boundaries | @tlduongducanh281-jpg | 4 | [#22](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/22) | P0 | OPEN | Todo |
| [#185](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/185) | Verify US04 completed counts with 19, 20 and 21 responses | @tlduongducanh281-jpg | 2 | [#50](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/50) | P0 | OPEN | Todo |
| [#186](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/186) | Complete role-specific post-logout and idempotent logout tests | @lesyhuy2k6-gif | 2 | [#183](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/183) | P0 | OPEN | Todo |
| [#187](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/187) | Verify the US02 three-active-evaluation acceptance example | @khuatnhatminhcfpro-cmyk | 1 | [#18](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/18) | P0 | OPEN | Todo |
| [#188](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/188) | Reconcile P0 acceptance messages, logout navigation and timing evidence | @khuatnhatminhcfpro-cmyk | 3 | Cross-story | P0 | OPEN | Todo |
| [#189](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/189) | Audit isolated database fixtures, foreign keys and rollback coverage | @lesyhuy2k6-gif | 3 | [#183](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/183) | P0 | OPEN | Todo |
| [#190](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/190) | Complete M4 clean-clone and independent review evidence | @lesyhuy2k6-gif | 2 | Cross-story | P1 | OPEN | Todo |

All tasks use milestone **Sprint 4 - M4 Automated Testing** (milestone #1); all five parent stories are included in that milestone and labeled P0. Ten story-specific task relationships use GitHub's actual parent/sub-issue links, not body text alone: #165→#14, #166→#18, #167→#22, #168→#50, #169→#183, #184→#22, #185→#50, #186→#183, #187→#18 and #189→#183. #189 also supports US03 integrity; cross-story #163/#164/#170/#171/#188/#190 list their related stories explicitly.

The 9 original tasks total **26 estimated hours**; the 7 supplemental tasks add **17 estimated hours**, for **43 hours of scoped estimates**. Open work is #163 (2h) plus the 17h follow-ups, or **19 estimated hours**. These are planning estimates, not time spent, approved capacity or completed velocity. Closed #164/#170/#171 retain their historical issue state; unverified coverage/evidence is tracked in follow-ups instead of claiming it was completed.

| Member | Responsibility | Total scoped estimates | Open estimates |
|---|---|---:|---:|
| Khuat Dinh Trung (@khuatnhatminhcfpro-cmyk) | US01, US02, M4 documentation/refinement, contract decisions | 15h | 6h |
| Duong Duc Anh (@tlduongducanh281-jpg) | US03, US04 | 13h | 6h |
| Le Sy Huy (@lesyhuy2k6-gif) | Database/repository integrity, fixtures, US11 and setup/evidence | 15h | 7h |

The five P0 story estimates sum to **18 story points** (3+3+5+5+2). They are separate from task hours. No Sprint 4 velocity is calculated from hours or from a snapshot taken after implementation.

## Implementation order and dependencies

1. Retain merged baselines #164–#170 and their tests; do not recreate or reopen them solely because new coverage is planned.
2. #188 documents the PO decision on exact messages, Due soon capitalization, logout navigation, copied-cookie expectations and a controlled three-second timing contract before related production changes. Performance evidence must state environment/load/measurement interval; overall pytest duration is not response-time evidence.
3. #184, #185, #186 and #187 implement their current-contract cases independently on clean branches with isolated data. #189 audits integrity/rollback and records real findings; it must not silently enable production foreign keys just to make tests pass.
4. #190 follows the coverage/contract outcomes, installs dependencies in a fresh environment, records actual test/CI results and verifies team review/submission artifacts. #171's earlier closure is not substituted for this evidence.
5. An independent teammate reviews each PR. Update mappings/results only after actual execution; do not skip failing tests. Update Board status and issue state according to evidence.

## Planned pytest coverage

Every NOT IMPLEMENTED row in [testing.md](testing.md) now includes an exact **proposed** node and a real open owner task. The names below are specifications; they are not asserted to exist or pass.

| Pending cases | Open task | Proposed pytest node / parameters |
|---|---|---|
| TC-21–TC-26 | [#184](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/184) | `tests/test_submission_workflow.py::test_submission_rating_boundaries[rating-N]`, N=0,1,2,4,5,6 |
| TC-27–TC-29 | [#184](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/184) | `tests/test_submission_workflow.py::test_submission_text_length_boundaries[length-N]`, N=1999,2000,2001 |
| TC-30–TC-31 | [#184](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/184) | `tests/test_submission_workflow.py::test_submission_required_question_count[answered-N]`, N=4,5 |
| TC-37; TC-US04-08/09 | [#185](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/185) | `tests/test_lecturer_feedback.py::test_feedback_completed_count[count-N]`, N=20,19,21 |
| TC-39 | [#186](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/186) | `tests/test_auth.py::test_student_page_denied_after_logout` |
| TC-40 | [#186](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/186) | `tests/test_auth.py::test_lecturer_feedback_denied_after_logout` |
| TC-41 | [#186](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/186) | `tests/test_auth.py::test_anonymous_logout_is_idempotent` |
| US02-L12 | [#187](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/187) | `tests/test_student_evaluations.py::test_student_evaluations_three_active` |

Use the exact deterministic inputs/expected outputs in testing.md and each issue. For invalid submissions assert no response/answer writes; for count examples seed distinct enrolled students and exclude drafts; logout must use real login followed by logout before access denial. Proposed time-dependent tests use a frozen application clock and fresh SQLite rather than data/edusurvey.db.

## Board application and completion evidence

[The verified Board register](sprint4-board.csv) contains all 16 tasks and five parent stories. Each row records the actual assignee, hours/story-point reference, native parent, repository milestone, Testing Priority, development Sprint, Testing Sprint and stored Status. Every row is marked re-read verified; the earlier permission blocker was resolved through the user's OAuth authorization.

The write/read audit established:

- All 21 expected issue items exist, including newly added missing items; no original Board item was removed.
- Testing Sprint is Sprint 4 for all 21, and Testing Priority matches each issue's P0/P1 label. The seven follow-ups are Todo; #163 is In Review; closed baseline issues remain Done.
- Every one of the 16 tasks has the expected positive Estimated hours value and responsible assignee. The 43h total / 19h open estimates agree with repository issue bodies.
- Tasks and restored US11 use the real Sprint 4 iteration. The four closed development stories keep their original Sprint 3 values; Testing Sprint provides the separate M4 coverage scope.
- Existing Point/Points values and all unrelated items' recorded field values are unchanged. Sprint configuration/dates are not rewritten.
- Ten native parent/sub-issue relationships were re-read successfully. Cross-story tasks remain explicitly linked by references rather than fake #0 parents.

A successful optional Board workflow alone was not used as proof: values were read back from GitHub after the updates. Parent-story Done status reflects historical feature completion, while unfinished M4 tests remain visible in the open follow-up tasks.

| Acceptance criterion | Evidence / state |
|---|---|
| All five P0 stories reviewed and included in Sprint 4 testing | Requirements/story audit; restored US11 #183; Testing Sprint = Sprint 4 on all five |
| At least three normal/error cases per story | Existing and planned cases in testing.md; all story counts exceed three |
| Applicable numerical limits cover below/at/above | US02/deadline boundaries exist; rating/text plans #184 and count examples #185 explicitly defined |
| Owners, hours and balanced responsibilities | Verified issue metadata and Board Estimated hours; all three members assigned |
| Parent relationships | Ten native links re-read; invalid #0/#1 references corrected |
| Every case maps to a real or planned pytest test | 79 existing mappings + 18 explicitly proposed nodes in open issues |
| Project Board Sprint/priority/status/estimate values | **Applied and re-read verified for all 21 items** using Testing Sprint/Testing Priority and preserved development iterations |
| Backlog ready and refinement closure | **Ready for independent review/implementation**; #163 is In Review and closes when its reviewed PR merges |

AI assistance: OpenAI Codex inspected repository/GitHub evidence, organized tasks and traceability, verified the baseline command, applied authorized Board updates and re-read the result. No sprint meeting, execution result or teammate review is fabricated.
