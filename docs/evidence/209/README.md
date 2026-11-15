# #209 README and demo-access evidence

Parent #200; depends on #201/#202 UI, #205 hosting and #207 CI. Client audit
date: **2026-11-16**. The README is prepared for review, **not a completed public
entry-point acceptance**: no running public HTTPS URL has been verified.

## Actual checks

| Artifact | Observed evidence | Scope / limitation |
|---|---|---|
| [release-discovery.json](release-discovery.json) | Repository homepage null; no GitHub deployments/releases, deployment Variables or environments; no supplied URL in #200/#205/#209 comments | Repository metadata only; it does not rule out an unreported external service |
| [badge-link-check.json](badge-link-check.json) | Actual GitHub badge SVG and workflow page returned HTTP 200; SVG title `CI - passing`; active `.github/workflows/ci.yml`, repository/main/push filters verified | CI badge, not public application uptime, deployment or approval evidence |
| [local-walkthrough.json](local-walkthrough.json) | Real Chromium laptop 1440×900 and phone 390×844 private contexts, canonical seed, all five P0 and all three advertised role accounts | Local loopback HTTP with fresh temporary SQLite per viewport; not public HTTPS or independent human testing |
| [Student laptop](student-reloaded-laptop.png) / [phone](student-reloaded-phone.png) | Real submit/success state remains after reload; exactly one submitted response and three answers | Synthetic local data only |
| [Lecturer laptop](lecturer-feedback-laptop.png) / [phone](lecturer-feedback-phone.png) | Same submitted comment visible in assigned lecturer feedback, completed count one; drafts excluded | Local seed/ownership, not proof of deployed accounts |
| [README check](readme-check.json) | Role rows, all five P0 guide anchors, relative files, badge targeting and explicit incomplete publication status | Structure/link checks do not meet the still-missing first-line/public-account criteria |

Operator: **OpenAI Codex, AI-assisted**, not a teammate or public tester. The
walkthrough opened the actual first page `/`, expanded **Try a demo account**,
signed in as student, used Start evaluation/Review answers/Submit evaluation,
reloaded and returned to My Evaluations. It then signed out, signed in as lecturer,
clicked Review feedback and read the persisted comment/count; finally it signed
out, signed in as administrator and verified My account, then signed out again.
After each sign-out the browser returned to Login and `/api/auth/me` returned 401.
API requests were assertions, not a substitute for clicking the UI workflow.

The first ad-hoc check incorrectly expected `/` to redirect to `/login`; actual
code serves the Login form directly at `/`. The corrected check verifies that
visible form and the README documents `/` or `/login` accurately. No application
code or existing test was changed. Questions are awaited before selecting both
ratings. App time was controlled; SQL timestamp defaults were not asserted.
Temporary database files were removed after execution. Separate fresh seeds per
viewport do not prove that an already-used public account has fresh work.

The README credentials are the deliberately public synthetic seed password and
emails, verified through real local login. No real university credentials,
provider tokens, production database, password hashes or environment secret
values are committed. A consumed shared response stays completed: operators
must supply fresh synthetic work rather than reset a live DB.

## Remaining public acceptance

| Required item | State / next concrete action |
|---|---|
| Actual running HTTPS URL as README first line | **Unresolved.** Asked the user for the URL; no reply at this audit. Render access is not connected/verified. Keep the honest pending notice; do not insert a guessed host, GitHub URL or loopback address as the application. |
| Clickable public UI links | **Unresolved.** Current table links open README walkthroughs and explicitly identify route text. After verifying the origin, add actual absolute UI links for Login, My Evaluations, available evaluation, lecturer feedback and the account page's Sign out control. Never link GitHub-relative `/login` or a POST API as a clickable UI. |
| Deployed seed/accounts and fresh private-browser tour | **Unresolved.** On the actual HTTPS page, verify all documented role credentials, assigned data, submission/reload, lecturer feedback and sign-out using fake data; retain URL/provider SHA/time/results. Local evidence is not substituted. |
| Actual hosting/storage/cold start | **Unresolved.** Confirm account/plan/mount and restart/redeploy preservation. Render Free limits are conditional official terms, not an observed EduSurvey deployment or measured cold-start result. |
| Independent teammate approval | **Pending** new #209 PR review; no self-merge or fabricated approval. |

When the real URL arrives, put that literal verified URL on line one, move the
title below it, verify each absolute app link and rerun the private-context guide
against that origin. Confirm source/seed alignment before replacing any account
details. Record real restart/reset behavior and the operator's keep-online policy.
Keep #209 open until those requirements and independent review are satisfied.

Official platform terms re-read for this draft:
[Render Free](https://render.com/docs/free), [persistent disks](https://render.com/docs/disks).
The existing Blueprint proposes paid persistent storage; it does not prove
that service has been provisioned. No paid resource was created by this task.
