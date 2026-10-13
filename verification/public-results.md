# Public cloud validation

Date: 2026-10-13, Asia/Seoul.

- Signup and login navigation links use the actual public HTTPS app URLs.
- General and monitor test accounts created through the actual Supabase-backed applications (201). Passwords are hashed; no credentials in this report.
- HTTPS login and proxy Cookie/Set-Cookie/CSRF work; both session cookies have Secure; failed general login=401 and successful login=200.
- Actual deployed post and note create/read/update succeed, persisted in separate Supabase projects. Anonymous post mutation=401 and missing CSRF=403.
- General HTTPS requests reach the monitor through the final server event token; login_failure/401 and login_success/200 are stored and queried through Next.
- Sentry exercise remains disabled (404); Next prevents browser event ingestion (404). Sentry dashboard reception is not configured.
- Own smoke-test posts and notes deleted; subsequent detail requests return 404. Existing data was not altered.
