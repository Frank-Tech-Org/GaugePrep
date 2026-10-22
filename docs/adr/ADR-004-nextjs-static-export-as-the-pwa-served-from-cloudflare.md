# ADR-004: Next.js static export as the PWA, served from Cloudflare

- Status: Accepted
- Date: 2026-10-22

## Context

Learners use mid-range phones on 3G. Public pages need search visibility. The PWA must cache media and survive connection loss. The free-tools rule applies to non-production environments.

## Decision

Build the PWA with Next.js 16 in static export mode (one HTML file per route), React and TypeScript, a Serwist service worker, an IndexedDB journal for the active session, and an API client generated from the backend OpenAPI contract. Serve it from Cloudflare, including the Douala data centre.

## Alternatives considered

- **Next.js with a Node server:** Rejected: a server to run for no need, since all logic is in the API.
- **Vite single-page app:** Rejected: no pre-rendered public pages without a second tool.

## Consequences

No frontend server to operate; edge delivery close to learners. Features needing a Next.js server (server actions, middleware, rewrites) are not used. iOS limits apply: no background sync, storage may be cleared, so the server stays the source of truth.

## Sources

- https://nextjs.org/docs/app/guides/static-exports
- https://nextjs.org/docs/app/guides/progressive-web-apps
- https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide
