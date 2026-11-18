# Live health dashboard — #258

Public UI: `/health/dashboard`. Readiness API: `/health` (unchanged).
Parent: M5 readiness/monitoring #206.

The dashboard is an independently rendered HTML shell. Its HTTP 200 means that
the presentation page loaded; the prominently labelled **HTTP Status Code** card
shows the actual response code received from `GET /health`, including **200 OK**
and **503 Service Unavailable**. Application and Database Status come only from
the returned JSON `status`/`database` fields. No status is hardcoded as healthy.

- Reuses EduSurvey's academic navy/blue design tokens, system typography and
  accessible focus treatment, with responsive cards and explicit loading/error states.
- Healthy presentation requires HTTP 200 and both JSON fields equal to `ok`.
  HTTP 503 is shown as unavailable, while each component retains its actual result.
- An absent network response is shown as **No HTTP response**, with unknown
  components. It is never fabricated as HTTP 503. Invalid JSON preserves any
  received HTTP code but does not claim a verified application/database state.
- Every new check clears old results, avoiding a stale healthy banner during a
  failed retry. Request timeout is eight seconds, including reading the JSON body.
- Manual refresh and optional 30-second refresh; automatic checks skip hidden tabs
  and never overlap. The checkbox is off by default. Request duration describes
  the browser's health request, not a BR8 application performance guarantee.
- Dashboard and fetch responses are not cached. The fetch omits credentials;
  the public HTML shell is exempt from account-lifecycle DB lookups, so it still
  renders with a signed cookie during a database outage. No private user data,
  internal exception messages or upstream response bodies are displayed.

No changes to `/health` implementation, JSON contract, actual HTTP statuses,
Render health-check configuration, CI/CD, database schema or production data.
No migration is required. Existing monitoring tools continue to use `/health`;
they must not be pointed at the HTML shell.

Validation: **412 tests passed, 0 skipped** across SQLite, isolated PostgreSQL
and Chromium. Ruff and diff checks pass; desktop/mobile 200/503 screenshots were
visually inspected. Existing tests/assertions remain unchanged.

Verification includes existing readiness/regression tests and new checks for:
JSON remaining JSON even with `Accept: text/html`, missing-DB HTML access with a
signed session, real 200/503 requests on desktop/phone, malformed JSON/network
failure and successful manual recovery. Screenshot evidence is captured by those
browser tests with `HEALTH_SCREENSHOT_DIR` set to an output directory.

[Healthy desktop](evidence/health-258/health-200-1440.png) ·
[Healthy phone](evidence/health-258/health-200-390.png) ·
[Unavailable desktop](evidence/health-258/health-503-1440.png) ·
[Unavailable phone](evidence/health-258/health-503-390.png).

All tests run against isolated local SQLite/PostgreSQL data. No production request,
merge or deployment is part of this change. After independent review/release,
open `/health/dashboard` on the existing application origin to use the UI.
