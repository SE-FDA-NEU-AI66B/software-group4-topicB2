# Consistent network failure and safe recovery — #260

Branch: `fix/network-error-recovery`. Parent stories: US02 #18, US03 #22,
US04 #50, US12 #192 and US13 #193. APIs, server business rules, P0 routes and
database schema/data are unchanged. No migration, merge or deployment.

## Shared state

`network.js` wraps the application's fetch calls without replacing native fetch.
Only a transport rejection is converted to `NetworkFailure`; HTTP responses are
returned unchanged. A shared, responsive alert shows a local Wi-Fi Off SVG,
**No internet connection**, contextual guidance and **Try Again**. It uses no
external assets or dependencies and does not expose exception payloads.

Student evaluation reads, Lecturer topic analysis, shared role workspaces and
Admin account management use this component. Login, password setup, logout and
session revalidation also use it. Existing local error messages remain for context.
HTTP 401 retains sign-in navigation, while 403/404, validation/business errors and
malformed JSON retain their existing handling; they do not show the offline alert.
The label describes a failed application network request; browser fetch alone
cannot prove whether its underlying cause was Wi-Fi, DNS or another transport issue.

Restoring browser connectivity does not synthesize success or automatically replay
writes. Try Again calls the relevant real API; the originating flow renders the
actual response. New attempts clear the previous offline alert, so a subsequent
HTTP rejection is not still labelled as offline. No page reload is used to retry
ordinary data/form requests.

## Input and write safety

| Flow | Recovery behavior |
| --- | --- |
| Student list, topic analysis, dashboards, Admin directory | Retry their existing read/load operation. |
| Question/draft loading | Reload from the APIs while merging local unsaved answers ahead of older saved draft values. |
| Saving a student draft | Explicit retry sends the current answer snapshot through the existing idempotent PUT; only a server-confirmed save displays success. |
| Submitting an evaluation | First read the student's evaluation status. If the server confirms Completed, display that result without another POST. Otherwise retry submission with existing answers; duplicate/deadline/required-answer constraints stay server-enforced. |
| Lecturer/Admin creation, role/lifecycle/membership writes, CSV confirmation | Refresh real server records; never blindly replay a potentially committed write. Forms/CSV remain available. Check the refreshed records before explicitly repeating an action. Lost one-time account invitation links must be reissued through the existing authorized flow. |
| CSV preview | Repeat preview/validation, which creates no accounts. |
| Password setup / logout | Explicit user retry only, using the original one-time-token / idempotent logout contracts. An expired/used token or HTTP rejection is never treated as success. |
| Browser-restored page | Hide private contents while checking `/api/auth/me`. A network failure keeps the page/input in memory and exposes the retry alert. A matching verified account restores the existing DOM without a reload. A changed account/role reloads through server authorization; 401 still goes to sign-in. |

No answers/passwords are written to localStorage or sessionStorage. Unsaved input
is kept in the current page's memory/DOM; closing or manually reloading a page is
not a persistence guarantee. A completed response is only displayed after a real
submission confirmation, duplicate-completion response or real Completed status.

## Verification

**420 tests passed, 0 skipped** in the full local SQLite/PostgreSQL/Chromium
regression; Ruff and diff checks pass. The 16 new browser cases also pass as a
focused run. Existing assertions/tests are not removed or weakened.

New Chromium tests simulate transport aborts/recovery for Student, Lecturer,
Admin dashboard and Admin provisioning at 1440px and 390px. They verify a real
200 response after Try Again and the actual recovered records, with no horizontal
overflow. Separate tests verify HTTP 401/403/404/409 are not labelled offline.

Persistence tests preserve ratings/text through failed draft save and verify the
saved answers after reload. Submission tests cover requests aborted before any
write and responses lost **after the real server committed**; the latter performs
no second POST. Both leave exactly one completed database response. Session
revalidation tests retain unsaved answers through a simulated network failure.
Existing P0 assertions remain intact.

Set `NETWORK_SCREENSHOT_DIR` when running the browser tests to regenerate evidence
from disposable local test data. No live production requests or data changes are
used by these checks.

| Flow | Desktop | Phone |
| --- | --- | --- |
| Student evaluations | [View](evidence/network-260/student-1440.png) | [View](evidence/network-260/student-390.png) |
| Lecturer feedback | [View](evidence/network-260/lecturer-1440.png) | [View](evidence/network-260/lecturer-390.png) |
| Admin workspace | [View](evidence/network-260/admin-1440.png) | [View](evidence/network-260/admin-390.png) |
| Admin accounts | [View](evidence/network-260/accounts-1440.png) | [View](evidence/network-260/accounts-390.png) |

This handles API failures on an already loaded application. If the initial HTML
or scripts cannot be downloaded, the browser's own network error remains in
charge; no offline application cache/service worker is introduced. The separate
health dashboard keeps its existing HTTP/no-response semantics.
