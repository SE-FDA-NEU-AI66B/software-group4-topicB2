# Sprint log

## Sprint 1 - 2 September 2026 to 15 September 2026

### Sprint goal

Complete the Milestone 1 requirements by defining the product vision, personas, scenarios, user stories, acceptance criteria, business rules, screens and flow diagram, and supporting project documentation.

### Required chore issues

| Issue | Owner | Closed? |
|---|---|---|
| #68 Refine backlog for Sprint 1 | @khuatnhatminhcfpro-cmyk (PO) | Yes |
| #70 Sprint 1 wrap-up | @lesyhuy2k6-gif (SM) | Yes |

### Committed

| Issue | Story Points | Owner |
|---|---|---|
| #61 Product Vision & Personas | 3 | @khuatnhatminhcfpro-cmyk |
| #62 Scenarios | 3 | @tlduongducanh281-jpg |
| #63 User Stories & Acceptance Criteria | 5 | @khuatnhatminhcfpro-cmyk |
| #64 Business Rules | 3 | @lesyhuy2k6-gif |
| #65 Screens & Flow Diagram | 3 | @khuatnhatminhcfpro-cmyk |
| #66 README & Sprint Log | 2 | @lesyhuy2k6-gif |
| #67 Create and Refine GitHub Story Issues | 4 | @khuatnhatminhcfpro-cmyk |
| #68 Refine backlog for Sprint 1 | 2 | @khuatnhatminhcfpro-cmyk |
| #69 Review requirements and prepare M1 submission | 2 | @tlduongducanh281-jpg |
| #70 Sprint 1 wrap-up | 2 | @lesyhuy2k6-gif |

**Total committed: 32 points**

### Result

| Issue | Points | Status | If not done, why |
|---|---|---|---|
| #61 | 3 | Done | |
| #62 | 3 | Done | |
| #63 | 5 | Done | |
| #64 | 3 | Done | |
| #65 | 3 | Done | |
| #66 | 2 | Done | |
| #67 | 4 | Done | |
| #68 | 2 | Done | |
| #69 | 2 | Done | |
| #70 | 2 | Done | |

**Completed: 32 points. Velocity this sprint: 32**

### Sprint Review

- What we demonstrated:
  - The completed Milestone 1 requirements document, including product vision, personas, scenarios, user stories, acceptance criteria, business rules, screens and flow diagram.
  - The refined GitHub backlog with aligned stories, tasks, priorities, and estimates.

- Feedback received:
  - The team confirmed that the requirements were clear, testable, and aligned with the project scope.

- Backlog changes as a result:
  - Reviewed and refined GitHub Issues.
  - Removed inconsistent or duplicated task requirements.
  - Updated relationships between stories and supporting tasks.

### Retrospective

| Keep doing | Stop doing | Start doing |
|---|---|---|
| Keep requirements and tasks clearly documented in GitHub. | Avoid leaving documentation updates until the end of the sprint. | Start reviewing backlog consistency earlier during the sprint. |

**One concrete action for next sprint (with an owner):**

Review task progress weekly and update the GitHub Project Board regularly — Owner: @lesyhuy2k6-gif

### Attendance

| Member | Planning | Review | Retro |
|---|---|---|---|
| @lesyhuy2k6-gif | Yes | Yes | Yes |
| @khuatnhatminhcfpro-cmyk | Yes | Yes | Yes |
| @tlduongducanh281-jpg | Yes | Yes | Yes |

### Scrum Master for Sprint 2

@tlduongducanh281-jpg
## Sprint 2

### Sprint Goal

Complete the Milestone 2 technical design and deliver a working EduSurvey walking skeleton connected to a real SQLite database.

### Sprint 2 Completed Work

During Sprint 2, the team completed requirements refinement, UML updates, technical design, database implementation, the walking skeleton, setup documentation, CI improvements, and design documentation.

Completed Sprint 2 issues include:

- #89 Clarify Lecturer and Administrator requirements — 2 points
- #90 Add administrator management requirements — 2 points
- #91 Add scenarios for key EduSurvey workflows — 3 points
- #92 Define EduSurvey response time requirement — 1 point
- #93 Update UML diagrams and link tasks — 3 points
- #98 Design EduSurvey architecture and API — 5 points
- #99 Design EduSurvey ERD and database schema — 5 points
- #100 Implement database initialization and seed data — 3 points
- #101 Implement EduSurvey walking skeleton — 5 points
- #102 Create SETUP guide and test the application — 3 points
- #103 Document design decisions and changes since M1 — 3 points
- #104 Refine backlog for Sprint 2 — 3 points
- #105 Sprint 2 wrap-up — 1 point
- #119 Fix CI checks for database schema and Python tests — 1 point

### Sprint 2 Metrics

| Metric | Result |
|---|---:|
| Sprint 2 issues | 14 |
| Final estimated scope | 40 points |
| Completed points | 40 points |
| Sprint velocity | 40 points |
| Completion rate | 100% |

Story points were finalized during the Sprint 2 wrap-up. The final estimated Sprint 2 scope was 40 points across 14 tracked issues. All Sprint 2 work was completed, resulting in a final velocity of 40 points.

### Walking Skeleton

The EduSurvey walking skeleton was successfully implemented using Flask, SQLite, and Jinja.

The end-to-end flow is:

`Browser → Flask Route → SQLite Database → Jinja Template → Browser`

The `/evaluations` route retrieves evaluation and course data from the SQLite database and renders the results in the browser.

The database is initialized using:

```bash
python3 src/init_db.py
```

The initialization script creates the EduSurvey schema and seeds 10 evaluations. The displayed evaluation data is retrieved from the database rather than from a hard-coded array.

### Sprint 2 Deliverables

The team completed the main Milestone 2 deliverables:

- Architecture design
- API design
- ERD and database schema
- Database initialization and seed data
- Working end-to-end walking skeleton
- `docs/design.md`
- `docs/SETUP.md`
- Architecture and ERD diagrams
- Updated UML diagrams
- CI smoke tests and schema compatibility fix
- Sprint 2 backlog refinement
- Sprint 2 Project Board review

### Sprint 2 Retrospective

#### What Went Well

- The team converted Milestone 1 requirements into a concrete technical design.
- The database schema was aligned with the EduSurvey domain model.
- A working Flask, SQLite, and Jinja walking skeleton was implemented successfully.
- Database initialization and seed data made the application reproducible.
- Pull requests and peer reviews were used to integrate Sprint 2 work.
- CI issues discovered during integration were documented and resolved through a separate issue.

#### What Could Be Improved

- Story points should be assigned during backlog refinement before implementation begins.
- Automated tests should be added together with implementation work.
- CI rules should be checked before introducing new project file types.
- Fresh-machine setup verification should be performed earlier in the sprint.

#### Actions for the Next Sprint

- Assign story points before starting the sprint.
- Add automated tests alongside new features.
- Keep CI configuration aligned with the project structure.
- Continue using focused issues, branches, pull requests, and peer reviews.
- Perform integration and setup verification earlier in the sprint.

### Sprint 2 Completion

Sprint 2 successfully delivered the Milestone 2 technical design and a working end-to-end EduSurvey walking skeleton backed by a real SQLite database.

The final Sprint 2 Project Board contains 14 tracked issues with a final estimated scope of 40 points. All planned Sprint 2 work was completed.
## Sprint 4

**Evidence qualification (#190, 2026-11-15):** the narrative below is the
historical #171 summary, not independently verified meeting attendance or M4
sign-off. Current [clean-clone/review evidence](m4-review-evidence.md) records
185 passed / 5 failed / 0 skipped at `686bd9e`, red main CI and unresolved Board
access/review evidence. Original issue closures are preserved. The later #163
refinement snapshot is also historical; #163 and #184–#189 are now closed,
while #183/#190 remain open. Task hours are estimates, not story-point velocity.

The subsequent user-authorized #190 CI remediation passed **190 tests in
51.40s** locally on Windows, resolving the five obsolete/platform-specific
test expectations. It does not retroactively change the baseline run or claim
independent human review and Board verification.

### Sprint Goal

Complete Sprint 4 deliverables, improve automated testing, finalize setup and testing documentation, and prepare the repository for Milestone 4 review.

### Sprint 4 Committed Work

| Issue | Description | Owner | Story Points |
|---|---|---|---:|
| #170 | Update setup guide with automated testing instructions | @lesyhuy2k6-gif | TBD |
| #171 | Sprint 4 wrap-up | @lesyhuy2k6-gif | TBD |

### Sprint 4 Completed Work

- Updated automated testing setup documentation.
- Added development and testing dependencies.
- Reviewed automated test execution instructions.
- Updated project documentation for Milestone 4.

### Sprint 4 Metrics

| Metric | Result |
|---|---:|
| Total committed issues | TBD |
| Completed issues | TBD |
| Committed story points | TBD |
| Completed story points | TBD |
| Sprint velocity | TBD |

### Sprint Review

- Reviewed Sprint 4 deliverables and acceptance criteria.
- Verified automated testing and CI results.
- Reviewed pull requests and documentation updates.
- Prepared project materials for Milestone 4 review.

### Retrospective

| Keep doing | Stop doing | Start doing |
|---|---|---|
| Maintain clear documentation. | Delaying testing until the end of the sprint. | Review pull requests earlier. |
| Use automated tests and CI. | Leaving issues without status updates. | Verify clean-clone setup regularly. |

### Sprint 4 Action Items

- Ensure all required pull requests are reviewed and merged.
- Verify automated tests pass.
- Complete testing and setup documentation.
- Prepare Milestone 4 submission materials.


### Sprint 4 Backlog Refinement - 2026-11-15 (#163)

The current audit is recorded in [sprint4-backlog.md](sprint4-backlog.md), with the verified Project field register in [sprint4-board.csv](sprint4-board.csv). This supplements the earlier summary; it does not claim that an additional sprint ceremony occurred.

- All five P0 stories are reviewed; the missing US11 story is restored as #183 and #169's invalid parent is corrected.
- Baseline tasks #164–#171 remain closed as recorded on GitHub. Seven open follow-ups #184–#190 cover the remaining numerical/acceptance examples, logout cases, contract decisions, database integrity and fresh-clone/review evidence.
- Every task has an owner, estimated hours, priority and Sprint 4 milestone. Task hours total 43 (26 original + 17 supplemental); open estimates total 19h including #163. These are planning estimates, not time spent or story-point velocity.
- `docs/testing.md` retains all original case IDs and mutation evidence; 97 cases comprise 79 existing mappings and 18 explicitly pending proposed tests.
- Current main `5a52af6`: `python -m pytest -v` produced **106 passed in 2.95s** locally. No implementation or test code changes are included in this refinement.
- After user-authorized Projects access, all **21 Board items** were updated and re-read successfully. Testing Sprint is Sprint 4 for all five P0 stories and all 16 tasks; Testing Priority, assignees and Estimated hours match the issue register. Existing development Sprint 3 values on closed stories and Point/Points values are preserved. #163 is In Review and closes through its reviewed PR; seven follow-ups remain Todo. The real Sprint 4 iteration (2026-11-01, 13 days, already completed) was reused without rewriting dates.

The existing TBD velocity fields above remain pending verified planning/closure evidence; hours must not be substituted for story points.
