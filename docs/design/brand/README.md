GaugePrep is an AI exam-prep web app for high-stakes language exams. It finds where a learner stands, trains them to exam-ready, rehearses the real exam with full timed simulations, and predicts the result in the exam's own scale with an honest range. The brand is **the honest gauge**: an expert with warmth, like a calm senior examiner who is on your side. It is a global brand that works in English and French from day one, on desktop, tablet and mobile web.

Three words carry everything: **Measure · Train · Rehearse**. Every screen, post and film should make one of them feel true.

## The idea behind the look

The mark is an open book whose pages fan into a gauge, inside a speech bubble. Pages already reached run from `sea` to `mist`; the `amber` page is your reading; the dim `unreached` page after it is the level still ahead. That one idea drives the system: amber always means "you, now", and there is only ever one amber thing in view.

## Colour

- Build screens from the semantic tokens: `bg` for the page, `surface` for cards and the exam sheet, `text` for copy, `text-muted` for secondary copy, `line` for dividers, `line-strong` for control borders. They switch for the dark theme on their own.
- `accent` (Amber) is for the reading and the one primary action per view. Put `on-accent` text on it, never white. Never set amber as text on `bg` or `paper` (1.9:1).
- The brand colours (`ink`, `depth`, `sea`, `lagoon`, `mist`, `unreached`, `amber`, `paper`) are fixed in both themes. Use them for brand moments: the gauge, dark bands, illustrations, social graphics. `sea`, `lagoon` and `mist` are never text on light grounds.
- Proportion on any marketing piece: about 60% Paper or Ink ground, 30% the teal family, 10% Amber.
- Errors use `danger` with a word and an icon, never colour alone. Success is said in words and shown on the gauge; there is no green.
- Contrast floor: body text 4.5:1 on its ground in both themes, large text and meaningful marks 3:1. Checked pairs: `text` on `bg` 11:1 light, 14:1 dark; `text-muted` on `bg` 5.3:1 light, 10.7:1 dark; `on-accent` on `accent` 5.8:1; `danger` on `surface` 5.8:1 light, 5.1:1 dark.
- Keyboard focus is a solid 2px `focus` ring with a 2px offset: Ink in light, Amber in dark.

## Type

- **Figtree** (`sans`) is the voice of the product: every screen, button, form and caption. It is also the face the wordmark was drawn from.
- **Fraunces** (`serif`) is for marketing headlines only: `headline-xl` and `headline-l` on the site, posters and social posts. Never inside the exam or for body copy.
- Product scale: `title-1` 32, `title-2` 24, `title-3` 19, `body-l` 18, `body` 16, `body-s` 14, `label` 13 in capitals, `score` 48 for the reading. Running copy never goes below 16px on mobile.
- Write numbers with tabular figures where they line up. Keep exam passages under `read-max` (680px) wide.
- Both families are OFL and ship in `fonts/` with Latin and Latin Extended, so French and German accents render.

## Layout and shape

- Spacing runs on a 4px base: `space-1` to `space-16`. Cards pad `space-4` on mobile and `space-6` above it; sections sit `space-12` apart on mobile, `space-16` on desktop.
- Design every screen at three sizes: mobile 360 to 430, tablet 768 to 1024, desktop 1280 and up, content capped at `content-max`.
- Corners are soft, like the bubble: `radius-md` for buttons and inputs, `radius-lg` for cards, `radius-full` for level badges and the gauge.
- Anything tappable is at least `tap-min` (44px). Learners are often on mid-range phones and costly data: keep pages light, no autoplay video, images compressed.
- Raise cards with `shadow-card` or separate them with `line`, not both.

## Imagery

- Real learners, real places, real devices: a person at a kitchen table with a phone, a library, a night bus. Natural light, warm skin tones rendered faithfully, diverse ages and countries. The brand is global; no single country, flag or landmark leads.
- Calm over hype: no confetti, trophies, rockets or fake leaderboards. Progress is shown on the gauge, not with celebration clip art.
- Never show exam-owner logos, papers or certificates. Name exams only descriptively ("TCF Canada", "IELTS") and never imply affiliation.
- 3D: use the rendered mark from the Renders group for hero moments and launch films; do not invent other 3D objects in a different style.

## Iconography

- Line icons, 1.75px stroke at 24px, rounded joins and caps, drawn in `currentColor` so they take `text` or `text-muted`. A free set that matches is Lucide (ISC licence).
- Icons sit beside a word, never instead of one, except universal controls (close, back, play).
- No emoji in product UI or brand graphics.
