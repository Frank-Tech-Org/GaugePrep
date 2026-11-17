# ADR-027: App and API hosts per environment, host-only cookies

- Status: Accepted (under D-11; the owner proposed the host names)
- Date: 2026-11-17

## Context

ADR-005 keeps sessions in cookies, which needs the app and the API on one registrable domain. The design doc names `app.` and `api.` for production only. Today `dev.gaugeprep.com` and `staging.gaugeprep.com` serve the API, and the web app lives on `*.pages.dev`, a different site, so a Lax session cookie would never reach the API. The accounts API sets cookies, so the hosts come first.

## Options considered

1. **Do nothing** (app on `*.pages.dev`): cross-site, so cookies need `SameSite=None` and third-party cookies, which Safari blocks by default. Breaks ADR-005.
2. **Nested hosts**: app on `dev.gaugeprep.com`, API on `api.dev.gaugeprep.com`; staging the same; production `app.` and `api.gaugeprep.com`. Same site everywhere. `api.dev` is a second-level name, so it stays DNS-only with kamal-proxy's own certificate, as the API is today.
3. **Flat hosts** (`api-dev.gaugeprep.com`): could sit behind the Cloudflare proxy, but breaks the production naming pattern and gains nothing while the API is DNS-only.
4. **Same origin through a Cloudflare Worker** proxying `/api`: no CORS, but a second deploy unit, an extra hop to the server, and a deviation from design doc 3.3.

## Evidence

- Same-site means same scheme and registrable domain; Lax cookies go with same-site fetches (RFC 6265bis, "same-site").
- Universal SSL covers the apex and first-level subdomains only (Cloudflare docs, Universal SSL limitations).
- On 2026-11-17 `dev` and `staging` resolve straight to the server (DNS-only); `api.dev` and `api.staging` have no record.
- The Cloudflare token in Doppler sees zero zones: it can edit Pages, not DNS.
- Django rejects an HTTPS write whose Origin is not the host or in `CSRF_TRUSTED_ORIGINS` (Django docs).
- Chromium caps `Access-Control-Max-Age` at 7200 seconds.

## Decision

Option 2.

| Environment | App | API |
|---|---|---|
| Local | `localhost:3000` | `localhost:8000` |
| Dev | `dev.gaugeprep.com` | `api.dev.gaugeprep.com` |
| Staging | `staging.gaugeprep.com` | `api.staging.gaugeprep.com` |
| Production | `app.gaugeprep.com` | `api.gaugeprep.com` |

- Cookies are host-only on the API host: no `Domain` attribute, so a dev cookie never reaches staging or production. Hosted names `__Host-gp_session` and `__Host-gp_csrf` (the browser then refuses a `Domain`), Secure, Path `/`, SameSite Lax, the session HttpOnly. Local uses `gp_session` and `gp_csrf` over HTTP.
- CSRF: the app cannot read the API's cookie, so `GET /api/v1/auth/csrf` returns the token in JSON; the app keeps it in memory and sends `X-CSRFToken` on every write. `CSRF_TRUSTED_ORIGINS` holds the app origin only.
- CORS: the exact app origin only, credentials allowed, headers `Content-Type`, `X-CSRFToken`, `Idempotency-Key`, max age 7200. A small backend middleware; `django-cors-headers` is refused because it is under 200 lines to write.
- One setting, `WEB_APP_ORIGIN`, feeds CORS and CSRF; `DJANGO_ALLOWED_HOSTS` is the API host.

## Consequences

- Good: one model in every environment; cookies can't cross environments; no new dependency.
- Bad: each JSON write pays one preflight per URL every two hours, one extra round trip on 3G. SSH and runbooks move to the server IP, since `dev.gaugeprep.com` moves to Pages. The deploy workflow's health host changes (owner-staged).
- Owner action: a Cloudflare token with DNS edit on `gaugeprep.com`, once; the records and Pages domains are then scripted.
- Design doc sections 11 and 14.2 change in this change.
- Checked by: tests on the `Set-Cookie` attributes and the CORS headers, added with the accounts API; none exists yet.

## Revisit when

The API moves behind the Cloudflare proxy, a native client needs tokens, or preflights show in the 3G budget.
