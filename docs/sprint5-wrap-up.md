# Sprint 5 wrap-up audit — not yet ready to close

Audit captured 2026-11-16T10:16:44.337606+07:00. Scrum Master: Khuất Đình Trung (@khuatnhatminhcfpro-cmyk), user-confirmed. Related [#212](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/212) / [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200). This is a delivery audit, not a claim of a completed ceremony, public release or submission.

## Scope and source limits

The core M5 plan is #200–212: 13 issues, 43 estimated hours. Hours are neither story points nor actual effort/capacity. The current Board Sprint 5 iteration is 2026-11-14–27; this is configuration, not an instructor-approved extension of the supplied 2026-11-13 00:00 deadline. Current Board assignments are not a historical sprint-start commitment baseline.

[API snapshot](evidence/212/github-audit.json) records issue states, direct PR authors, merge actors, review bodies/inline comments, head check rollups, iterations and effective main rules. PR selection initially follows issue references/milestone; the explicit counted list excludes incidental Sprint 4 PRs #217/#220/#222. Check rollups are observed current head statuses, not a reconstructed timeline proving every check was green at the merge instant. Pagination flags are retained. The 100 most recently updated open/merged PRs were cross-checked against all 30 PRs created since November 14; the index is in the snapshot. Closed/unmerged #231 is an intentional red-CI rehearsal, not delivered work. Review findings apply to the core M5 PR scope; no ordinary issue comments are counted as Review changes.

## Merged work and independent approvals

Ten explicitly M5 implementation PRs are merged, with SUCCESS head rollups and independent approvals. This exceeds four, but does not satisfy the separate per-member substantive-review gate. Integration/merge actors are not credited as feature authors.

| PR / delivery | Direct author | Independent approval | Observed head checks |
|---|---|---|---|
| [#218](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/218) [#201] Complete student P0 navigation and sign-out | @khuatnhatminhcfpro-cmyk | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/218#pullrequestreview-5910888060) | SUCCESS |
| [#219](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/219) [#202] Complete lecturer feedback navigation and error UX | @khuatnhatminhcfpro-cmyk | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/219#pullrequestreview-5911087930) | SUCCESS |
| [#223](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/223) [#214] Complete P0 backend contracts and M5 runtime readiness | @khuatnhatminhcfpro-cmyk | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/223#pullrequestreview-5911326833) | SUCCESS |
| [#225](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/225) [#203] Prepare UI before/after evidence and identify missing M3 sources | @tlduongducanh281-jpg | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/225#pullrequestreview-5911516759) | SUCCESS |
| [#226](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/226) [#205] Prepare persistent Render deployment and green-gated releases | @tlduongducanh281-jpg | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/226#pullrequestreview-5911532224) | SUCCESS |
| [#228](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/228) [#206] Add database readiness and sanitized request monitoring | @tlduongducanh281-jpg | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/228#pullrequestreview-5911637147) | SUCCESS |
| [#229](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/229) [#204] Prepare safe production SQLite and verified backup recovery | @lesyhuy2k6-gif | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/229#pullrequestreview-5911790957) | SUCCESS |
| [#230](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/230) [#210] Record P0 verification and safe M4 mutation rehearsal | @tlduongducanh281-jpg | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/230#pullrequestreview-5911829903) | SUCCESS |
| [#232](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/232) [#207] Gate production releases and prepare enforced main protection | @lesyhuy2k6-gif | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/232#pullrequestreview-5911865020) | SUCCESS |
| [#233](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/233) [#208] Prepare six-section M5 operations handover and evidence register | @lesyhuy2k6-gif | [Review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/233#pullrequestreview-5912048627) | SUCCESS |

## Individual contribution gate

| Member | Direct-authored merged PR | Closed assigned issue / actual closer | Substantive Review changes given |
|---|---|---|---|
| Khuất Đình Trung | [#218](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/218), [#219](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/219), [#223](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/223) | [#201](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/201) / Trung | **Pending**: observed approvals have no review body/inline content. Ordinary comments are excluded. |
| Dương Đức Anh | [#225](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/225), [#226](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/226), [#228](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/228), [#230](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/230) | [#203](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/203), [#205](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/205), [#206](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/206), [#210](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/210) / Đức Anh | **Pending**: observed approvals have no review body/inline content. |
| Lê Sỹ Huy | [#229](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/229), [#232](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/232), [#233](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/233) | [#204](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/204), [#207](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/207) / Huy | [PR #223 review](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/223#pullrequestreview-5911326833) identifies backup-failure/source preservation and restore-overwrite risks. Also concrete gaps on #225/#226/#228/#230. |

The two pending members must independently inspect a teammate’s change and submit a genuine review through Review changes. Do not manufacture review text, backdate activity or self-approve. Existing empty approvals remain valid approval records but cannot establish substantive feedback.

## Core task reconciliation

| Task | GitHub state at capture | Owner | Estimated hours |
|---|---|---|---|
| [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200) [Chore] Plan and track Sprint 5 M5 delivery | open | @khuatnhatminhcfpro-cmyk | 2 |
| [#201](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/201) [Task] Complete public student P0 navigation and sign-out | closed | @khuatnhatminhcfpro-cmyk | 4 |
| [#202](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/202) [Task] Complete public lecturer P0 feedback navigation and error UX | closed | @khuatnhatminhcfpro-cmyk | 3 |
| [#203](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/203) [Task] Capture two verified UI improvements from M3 feedback | closed | @tlduongducanh281-jpg | 2 |
| [#204](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/204) [Task] Prepare production database, demo data and backup recovery | closed | @lesyhuy2k6-gif | 5 |
| [#205](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/205) [Task] Deploy EduSurvey to a public HTTPS URL with green-gated releases | closed | @tlduongducanh281-jpg | 5 |
| [#206](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/206) [Task] Implement database-aware health checks and sanitized request monitoring | closed | @tlduongducanh281-jpg | 3 |
| [#207](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/207) [Task] Gate production deployment with CI and protect main | closed | @lesyhuy2k6-gif | 4 |
| [#208](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/208) [Task] Write and review M5 operations handover | open | @lesyhuy2k6-gif | 4 |
| [#209](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/209) [Task] Publish M5 README entry point and safe demo access guide | open | @lesyhuy2k6-gif | 2 |
| [#210](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/210) [Task] Verify every P0 on the deployed URL and rehearse M4 test evidence | closed | @tlduongducanh281-jpg | 4 |
| [#211](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/211) [Task] Prepare v1.0 release, final demo and M5 submission PDF | open | @khuatnhatminhcfpro-cmyk | 3 |
| [#212](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/212) [Chore] Sprint 5 wrap-up | open | @khuatnhatminhcfpro-cmyk | 2 |

Eight core issues are closed (#201–207 and #210); five remain open (#200/#208/#209/#211/#212). A closed issue is a source fact, not proof of every acceptance criterion. In particular #205/#210 closure does not erase their missing deployed evidence. #208 remains open despite merged handover PR #233.

Current Board Sprint 5 issue scope: [#200](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/200), [#201](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/201), [#202](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/202), [#203](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/203), [#204](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/204), [#205](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/205), [#206](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/206), [#207](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/207), [#208](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/208), [#209](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/209), [#210](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/210), [#211](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/211), [#212](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/issues/212). P1 administration/reporting work is separate from the five P0 release gates; retain unfinished items instead of claiming them delivered.

## Final acceptance and unresolved work

| Gate | Verified evidence / remaining action | Owner |
|---|---|---|
| Main CI | [Green run](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43744066081) on `7c0b06e36fff7690db9f6cec3d9d28a4e0503c92`; 257 tests in this main run. A new commit needs fresh evidence. | Team |
| Protected main | Effective organization rules require one approval, prevent deletion/force pushes. **No required_status_checks rule observed**: named green-check enforcement remains unresolved; see snapshot. Green CI alone is insufficient. | Huy / repository administrator, #207/#200 |
| Five P0 workflows | US01/02/03/04/11 have local tests and [local release rehearsal](p0-release-verification.md). Public private-desktop/phone, persistence and ≤3,000ms visible-outcome checks remain pending on the actual deployed SHA. Copied-cookie revocation is not claimed. | Đức Anh, #210/#205 |
| Public HTTPS / deployment identity | Repository homepage is empty; release/deployment API lists are empty. These observations do not exclude an unreported external service. Supply actual URL, verify reachability, /health, database behavior, deploy SHA and rollback evidence. | Đức Anh, #205/#206 |
| M3 improvements | [Local before/after documentation](ui-improvements-m3.md) exists; original feedback provenance remains pending. | Đức Anh, #203 |
| Operations / README | [Handover](operations.md) exists; real platform access, alert delivery and production recovery evidence remain pending. README work is in [open PR #235](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/235). | Huy, #208/#209 |
| Monitoring / keep online | Operations assigns monitoring to Đức Anh (every minute during active release/demo; daily otherwise). Automated monitoring, hosted evidence and instructor-confirmed keep-online date remain unverified. Trung confirms date; Đức Anh confirms hosting access. | Đức Anh / Trung |
| v1.0 / PDF / demo | [Open preparation PR #238](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/238) contains a draft, not final submission. Exact deployed release SHA, published v1.0, confirmed student IDs, final PDF, verified links, genuine 12+5 rehearsal and instructor late-submission arrangement remain pending. No upload/rehearsal claimed. | Trung, #211 |
| Story points / velocity | No sprint-start baseline or reliable completed-point reconciliation found; see [five-sprint table](sprint-log.md#five-sprint-metrics-audit). Recover planning/closure evidence before reporting numeric velocity. | Trung / team |

## Board and closure rule

#212 is In Progress during this audit and moves to In Review with its focused PR. #200 remains open. Preserve other task statuses and historical closures; they are not silently upgraded to verified release acceptance. Do not close #212 until the unresolved rows and individual-review gate have evidence and independent review. No automatic self-merge or approval.

AI assistance: Codex — documentation and verification support.
