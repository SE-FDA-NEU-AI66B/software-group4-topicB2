# Coherent academic UI — #252

Branch: `feature/coherent-academic-ui`. Parent stories: US01 #14, US02 #18,
US03 #22, US04 #50, US12 #192 and US13 #193. Original acceptance criteria,
routes, role authorization and submission rules are unchanged.

## Audit findings and changes

| Area | Finding | Change |
| --- | --- | --- |
| Design | Student list/taking pages already had mature cards, validation and mobile behavior; workspace used independent styles and spacing. | Retain those components; share navy/blue tokens, typography, focus treatment, sidebar and responsive navigation across authenticated pages. Login retains its split-panel layout and adopts the same palette. |
| Navigation | Different headers and isolated role links; old Student menu was coupled to its own sidebar. | Shared role-aware Jinja navigation and one keyboard/mobile controller, current-page state, skip link and Escape/focus return. Keep the Student search shortcut. |
| Dashboard | Long course list before useful tasks, sparse metrics and undifferentiated forms. | Place evaluation tasks first, show counts/progress based on real API records, status filters, course search, response progress and direct analytics links. |
| Lecturer | One basic question field and no student-facing preview. | Add/remove any number of rating/text questions, configurable required flags, accessible modal preview, ordered saved-question preview, explicit open/close. |
| Admin | Directory, course creation and assignment forms visually blended together; wide table awkward on phones. | Searchable account directory, separate administration panels and stacked phone records with role controls visible. Existing last-admin/course-role guards remain server-enforced. |
| Taking a survey | Existing progress and rating UI was stronger than the workspace, but draft state was unclear. | Preserve question cards/rating controls; group explicitly topic-prefixed questions; show unsaved/saving/saved/restored/error draft states. |
| Sample data | `src/init_db.py` has three question templates. Schema supports unlimited ordered questions; API accepts any non-empty rating/text list. `enrich_demo.py` has a separate legacy five-question fixture. | Leave existing fixtures/data intact. Add explicit `--rich` pack creating six NEW `DEMO-RICH-*` courses and comprehensive surveys. |

## Design system and accessibility checks

`design-system.css` provides shared tokens, app shell and responsive breakpoints;
page CSS retains domain-specific layouts. `app_navigation.html`/`.js` provide
role-aware navigation without duplicating logout controls. Workspace templates and
scripts use textContent for API content, native labelled controls, fieldsets,
progress elements, live status messages and a native preview dialog.

Checks include 1440×1000 desktop, 820×1180 tablet and 390×844 phone captures;
no document-level horizontal overflow, JavaScript exceptions or visible form
controls missing a programmatic label in the captured screens. Keyboard tests
cover rating selection, modal Escape/focus return and mobile navigation Escape.
Shared colors use dark text on light surfaces, and focus outlines are visible.
Reduced motion is respected. This is not a comprehensive assistive-technology or
formal WCAG certification; screen-reader usability remains a manual follow-up.

## Explicit rich demo pack (review before applying)

No seed is executed at startup, build or deployment. No migration is required.
The existing legacy seed behavior and its exact tests remain intact.

Set `EDUSURVEY_DEMO_DATABASE` to an **isolated, migrated demo database**, and
`EDUSURVEY_DEMO_PASSWORD` to a chosen credential of at least 12 characters, then:

```sh
python tools/enrich_demo.py --rich
```

This creates six new courses, 6 surveys, 60 questions and 66 synthetic completed
responses, reusing matching-role demo accounts. The default template has eight
rating questions and two optional written questions, covering teaching quality,
course content, learning materials, assessment and overall satisfaction. Existing
surveys and submitted answers are never updated. A second run adds zero records.
The production-runtime CLI guard remains in place.

For a different question count or wording, use a JSON array of objects with
`question_text`, `question_type` (`rating`/`text`) and optional boolean `is_required`:

```sh
python tools/enrich_demo.py --rich --questions-file /path/to/questions.json
```

There is no fixed count in the schema, creation API, builder, renderer or seed
loop. Ten is the default template size; tests also exercise twelve configured
questions. Changing the JSON does not rewrite an already seeded pack. Use a fresh
isolated database for another rehearsal configuration. Never reset production.

## Reproduce screenshot evidence

With development dependencies and Chromium installed:

```sh
python tools/capture_role_ui.py --output /tmp/edusurvey-ui-evidence
```

Optionally set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to an existing Chrome executable.
The helper creates a fresh temporary database, generates a random demo credential,
captures the screens and removes the temporary database. It never reads production
credentials or data. [Evidence manifest](evidence/ui-252/manifest.json) records 27
role/viewport checks; the directory includes 30 screenshots (three additional
scrolled Admin-directory captures).

| Screen | Desktop | Phone |
| --- | --- | --- |
| Login | [View](evidence/ui-252/login-desktop.png) | [View](evidence/ui-252/login-phone.png) |
| Student dashboard | [View](evidence/ui-252/student-dashboard-desktop.png) | [View](evidence/ui-252/student-dashboard-phone.png) |
| Existing evaluation list | [View](evidence/ui-252/student-evaluations-desktop.png) | [View](evidence/ui-252/student-evaluations-phone.png) |
| Ten-question survey | [View](evidence/ui-252/student-survey-desktop.png) | [View](evidence/ui-252/student-survey-phone.png) |
| Lecturer management | [View](evidence/ui-252/lecturer-management-desktop.png) | [View](evidence/ui-252/lecturer-management-phone.png) |
| Feedback analytics | [View](evidence/ui-252/lecturer-feedback-desktop.png) | [View](evidence/ui-252/lecturer-feedback-phone.png) |
| Admin dashboard | [View](evidence/ui-252/admin-dashboard-desktop.png) | [View](evidence/ui-252/admin-dashboard-phone.png) |
| Admin directory | [View](evidence/ui-252/admin-directory-desktop.png) | [View](evidence/ui-252/admin-directory-phone.png) |

Tablet captures are linked from the manifest. Screenshots contain only generated
synthetic accounts. CI/test results are recorded on the PR and issue #252.

## Validation

- Full local regression: **380 passed, 0 skipped**, including unchanged P0 tests,
  SQLite, dedicated PostgreSQL UTF-8 and Chromium.
- Ruff and `git diff --check`: passed.
- All 27 capture scenarios: HTTP 200, no JavaScript exceptions, no page overflow,
  no visible controls missing labels. Thirty screenshots are included above.
- Existing test functions/assertions remain intact. New tests add mixed-type
  question preview and persistence, optional questions, three viewport layouts,
  mobile navigation, dashboard filtering, role rejection and rich-pack safety.
- Feedback dates use readable local presentation with the original timestamp
  retained in semantic `time` markup. The capture helper exercises that enhancement.

## Scope still incomplete

This is a UI/workflow polish change, not an expansion into full university SIS
administration. Account provisioning/deletion, removing/reassigning memberships,
system settings, outbound reminders, advanced exports and comparison analytics
still need backend work. The UI presents the management actions supported by
existing APIs; it does not imply unavailable operations are implemented. Auth
redirect destinations are preserved for P0 compatibility. Production appearance
and deployed interaction latency remain unverified until a separately approved
release. No automatic merge, deployment or production seeding is part of this task.
