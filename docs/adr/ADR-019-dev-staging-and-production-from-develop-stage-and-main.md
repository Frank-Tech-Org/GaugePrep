# ADR-019: Dev, staging and production from develop, stage and main

- Status: Accepted
- Date: 2026-10-29

## Context

`develop` deployed straight to staging, and releases were cut on `release/*` branches. Agents merge into `develop` several times a day, so staging changed under the release gate and the owner's Friday demo. The owner asked for three long-lived branches: `main`, `stage` and `develop`, with `develop` the default.

## Decision

Each long-lived branch has its own environment, and code only moves forward:

- `develop` (default) deploys to **dev** on every merge. Each ticket is QA'd there.
- `stage` deploys to **staging**. The owner promotes `develop` into it with a merge commit; the release gate, regression and the weekly demo run there.
- `main` deploys to **production** on a version tag. The owner merges `stage` into it with a merge commit.

Dev and staging share the Oracle Always Free server as two Kamal deploys, each with its own Neon branch and R2 bucket. Dev uses a fake SMS provider and the cheapest AI models. `release/*` branches are dropped. A defect found on staging is fixed on `develop` and promoted again. Only a hotfix starts on `main`, and it is merged back into `stage`, then `develop`.

## Alternatives considered

- **Keep `develop` to staging with `release/*` branches:** no new environment, but staging changes during the gate and the demo.
- **A `stage` branch with no environment of its own:** an extra merge step with nothing behind it.
- **A preview environment per PR:** more hosting for little gain now; free PWA-only previews can be added later.

## Consequences

- Four places run the code: local, dev, staging and production, plus throwaway CI runs.
- The Oracle server must fit two deploys within 2 OCPU and 12 GB. If it doesn't, a paid dev host is an owner decision.
- AI and SMS spend stays low in dev by configuration.
- Promotions must be merge commits, never squash, or `stage` and `main` drift from `develop`.
- `merge.sh` is unchanged: agents merge only into `develop`. The owner merges into `stage` and `main`, and the push alarm covers both.
