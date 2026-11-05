---
name: branches-and-environments
description: develop→dev, stage→staging, main→production; promotions by owner merge commits; the app is a responsive web app plus PWA, never framed as mobile
metadata:
  type: project
---

On 2026-10-29 the owner asked for three long-lived branches, `main`, `stage` and `develop` (default), and approved the CTO model in ADR-019: `develop` deploys to dev (ticket QA), `stage` to staging (release gate, regression, Friday demo), `main` to production on a tag. `release/*` branches are gone; the owner merges `develop → stage` and `stage → main` with merge commits; a hotfix is merged back into `stage`, then `develop`. Dev and staging share the Oracle Always Free server.

The owner also said GaugePrep is a responsive web app at every breakpoint, plus PWA, and felt "mobile" was over-said; on 2026-11-05 the owner approved dropping "mobile-first" from the product description. Test and describe at phone and desktop sizes, never "phone only"; a smartphone is a screen size and device class, not the product.

**Why:** a stable staging for the demo and the gate while agents keep merging into `develop`.
**How to apply:** QA targets dev; the gate and demo target staging; never fix on `stage`, fix on `develop` and promote again. See [[agents-commit-owner-merges]] and [[notion-weekly-demos]].
