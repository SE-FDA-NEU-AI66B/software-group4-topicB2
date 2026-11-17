# Role workspace and survey lifecycle — #248

Parent stories: US13 #193 / tasks #197 #198 #199, US08, US12 #192,
US02 #18, US03 #22, US04 #50. Original acceptance criteria remain unchanged.

## Implemented behavior

- `/dashboard` offers course search and role-specific navigation. Student progress
  comes from the existing assigned-evaluation API, including Completed/Due soon.
- `/lecturer/evaluations` lists only assigned courses and their evaluations.
  A lecturer configures ordered rating/text questions, saves a draft, reviews its
  questions and opens or closes it. `/admin/evaluations` reuses that workflow
  with system-wide course access. Creation remains draft-first; publishing is explicit.
- `/admin/users` includes the account directory, guarded role changes, course
  creation and adding student enrollment/lecturer assignment. Existing course
  relationships prevent incompatible role changes; the last administrator is retained.
- Students explicitly save incomplete answers through the draft endpoint. Refresh
  restores the saved answers; submission uses the original validation and duplicate
  enforcement. Saving a draft cannot overwrite submitted feedback.
- All new mutations validate database roles and course ownership. PostgreSQL
  evaluation lifecycle and submission/draft writes coordinate through shared/exclusive
  transaction advisory locks. SQLite serializes writes with BEGIN IMMEDIATE.
- No schema migration, production seed, release-tag movement or automatic merge.

## API additions

| Endpoint | Authorization |
| --- | --- |
| GET `/api/workspace` | Authenticated; role-scoped records, never password hashes |
| GET/PUT `/api/evaluations/:id/draft` | Enrolled Student; PUT requires open, future evaluation |
| PATCH `/api/evaluations/:id/status` | Assigned Lecturer or Administrator |
| POST `/api/admin/courses` | Administrator; duplicate code returns 409 |
| POST `/api/admin/course-memberships` | Administrator; validates Student/Lecturer role, duplicate returns 409 |
| PATCH `/api/admin/users/:id/role` | Administrator; last-admin and relationship guards |

Deadline input in the UI uses browser local time, converted to ISO UTC. Legacy
naive creation timestamps are interpreted as UTC for new lifecycle validation.
A submitted response is final; draft editing only applies before submission.

## Verification and remaining acceptance work

Existing tests are preserved. New SQLite, PostgreSQL and Chromium tests cover
creation/publishing, exactly five questions, denied cross-course access, draft
persistence, invalid-input rollback, role revocation, duplicate memberships and
last-admin protection. Chromium covers laptop and phone layouts. Test duration is
not evidence of deployed BR8 latency; measure warm/cold production separately after
approved deployment. GitHub Actions remains the authoritative merge/deploy gate.

Still outside this delivery: full account provisioning/deletion, removal/reassignment
of existing memberships, system-settings persistence, general question editing after
creation, automated outbound reminder delivery, export and advanced comparative
analytics. Existing feedback grouping/statistics and student filtering remain available.

## Research basis

[Qualtrics course evaluations](https://www.qualtrics.com/support/course-evaluations/course-evaluations-overview/)
organizes the workflow around evaluations, reminders and results.
[Explorance Blue](https://www.explorance.com/products/blue/) emphasizes collection,
analysis and distribution of feedback. The implementation prioritizes those workflow
connections using the existing EduSurvey requirements; LMS integration and AI analysis
are not added to the acceptance scope.
