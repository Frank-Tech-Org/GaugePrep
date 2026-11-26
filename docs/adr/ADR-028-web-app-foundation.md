# ADR-028: Web app foundation with the fewest runtime packages

- Status: Accepted (CTO, under D-11)
- Date: 2026-11-26

## Context

ADR-004 fixes Next.js 16 static export, React, TypeScript and a Serwist service worker; the design doc adds message catalogues for French and English. Neither says how catalogues, styles, tokens, fonts and the worker are built. The approved design needs French and English, light and dark, phone to desktop, and Figtree plus Fraunces.

## Options considered

1. **Do nothing**: each web ticket picks its own; the shell, the auth screens and onboarding would add overlapping packages to one lockfile.
2. **Library stack**: Tailwind CSS, `next-intl` and `@serwist/turbopack`. More packages to audit; the Serwist Turbopack route is labelled experimental.
3. **Own code on platform features**: CSS Modules and the brand tokens as CSS variables; a typed catalogue lookup with `Intl` for plurals, dates and numbers; Serwist through `@serwist/cli` run on the export output; self-hosted Latin subset fonts.
4. **Webpack build** with `@serwist/next`: works, but gives up the default bundler and needs `next build --webpack`.

## Evidence

- Next.js 16.4.6 is the latest stable (9 November 2026, GitHub releases); 16.4.1 fixed critical RCE flaws, so the floor is 16.4.6.
- Measured 2026-11-26: a one-button page on 16.4.6 static export loads 135 KB of gzipped JavaScript, polyfills excluded.
- A Turbopack `next build` fails when the config has a `webpack` key (Next.js 16 upgrade guide); `@serwist/turbopack` builds the worker in a route handler and its docs call it experimental (serwist.pages.dev/docs/next/turbo).
- Measured 2026-11-26: Figtree Latin subset 18 KB; Fraunces full 188 KB, Latin variable 117 KB, one static weight (600, opsz 72) 17 KB.
- Static export has no middleware (ADR-004), so locale detection runs in the browser.

## Decision

Option 3.

- Styles: CSS Modules plus one global tokens file generated from the brand `tokens.json`. Dark theme by `prefers-color-scheme` unless the learner picks one; the choice sits on `<html data-theme>`, set by a small inline script before paint.
- Text: one JSON catalogue per feature and language (`messages/<lang>/<feature>.json`), so parallel tickets never edit the same file. A test fails on a key missing in one language. Learner routes carry no locale segment; public pages get `/fr` and `/en` when they are built.
- Worker: `serwist` and `@serwist/cli`, run after `next build` on the export output.
- Fonts: self-hosted WOFF2, Latin subset, `font-display: swap`. Figtree everywhere. Fraunces only as the 17 KB static instance, on the auth titles and carousel the owner approved and on public pages; never in the level test, the exam or body copy.
- Images: none without a recorded source and licence; auth carousel photos load at tablet width and up only, through `<picture>` media queries.
- Tests: Vitest with React Testing Library; Playwright with axe-core (ADR-021).

## Consequences

- Good: no CSS or i18n runtime package; parallel tickets own separate catalogue and style files.
- Bad: we own about 150 lines of catalogue code and the token build; ICU message syntax is out.
- Bad: 135 KB of framework JavaScript leaves no room under a 100 KB per-route limit; the performance engineer sets the route budget from the shell's measured number.
- Checked by: the catalogue parity test and the route JavaScript check in CI, both added with the shell; none exists yet.

## Revisit when

The shell misses usable-under-3 s on slow 3G (then ADR-004 reopens), Serwist calls its Turbopack mode stable, or a screen needs ICU plurals `Intl` cannot give.
