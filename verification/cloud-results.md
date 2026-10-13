# Day2 local validation

Date: 2026-10-13 (Asia/Seoul). External cloud services were not deployed.

- Both Compose configs pass; general /health=200; Next blocks browser event ingestion; anonymous monitor /me=401.
- General failed/successful logins return 401/200; Next forwards Set-Cookie, Cookie, login status and CSRF token.
- Posts and notes create/read/update use separate real PostgreSQL databases; notes reject missing CSRF=403 and blank input=400; login_failure/401 and login_success/200 are stored and queried.
- After recreation of all seven containers, posts, notes, user hashes and both signed login sessions remain valid.
- Stopped monitor API: Next returns 502 with the documented error message.
- After restoring monitor API, the same events request succeeds=200.
- Post/note deletes succeed and deleted details return 404; proxied logout=200. Smoke-test fixtures were cleaned up.

## Production builds and regression tests

- All three app-level Docker build contexts succeeded. Flask images ran the final application with Waitress.
- Next.js 16.4.0 production builds succeeded both on the host and in Docker with no MONITOR_API_URL or database settings.
- General real-PostgreSQL regression suite: 12 tests passed, disposable schema removed after testing.
- Monitor real-PostgreSQL, signup proxy and health suite: 14 tests passed, disposable schema removed after testing.
- Sentry contract suite: 2 tests passed in the final general image. Disabled endpoint=404, anonymous=401, authenticated enabled endpoint=200/result 1.0. Privacy filter and SDK options validated without contacting Sentry.
- Exercise image from commit 192144b reproduced ZeroDivisionError/500 under the same authenticated/feature-enabled conditions. Final fix is commit 853988b.

## Browser verification

- Logged in through Next; the dashboard displayed login_failure/401 and login_success/200: [dashboard-cloud.jpg](dashboard-cloud.jpg).
- Created note #2 through the screen and reloaded; the same title and complete body were re-read: [note-cloud.jpg](note-cloud.jpg).
- Stopped monitor API; the screen displayed the documented connection error and the refresh button became enabled again: [api-error-cloud.jpg](api-error-cloud.jpg).
- Restored/rebuilt the final API and clicked the same refresh button; the error disappeared and the same saved note remained: [retry-recovered-cloud.jpg](retry-recovered-cloud.jpg).
- These are local app screenshots. They do not prove Render deployment, Supabase connectivity or Sentry reception.
