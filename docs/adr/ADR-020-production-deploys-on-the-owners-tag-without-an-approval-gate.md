# ADR-020: Production deploys on the owner's tag, without an approval gate

- Status: Accepted
- Date: 2026-10-30

## Context

Production deploys only from a version tag `vX.Y.Z` on a commit that is on `main`; `main` never deploys by itself. The production deploy workflow must know whether the tag deploys at once or waits for an approval. One person operates the system, so a second approver does not exist. The repository is private, in the `LinguaMentor` organisation on GitHub's free plan (owner decision D-6).

On that plan GitHub gives a private repository no environments, so no required reviewers and no deployment protection rules: "Organizations with GitHub Team and users with GitHub Pro can configure environments for private repositories", and "If you are on a GitHub Free, GitHub Pro, or GitHub Team plan, required reviewers are only available for public repositories." Rulesets, including tag rulesets, are also listed only for Team and Enterprise on private repositories, so tag creation cannot be restricted on GitHub either.

## Decision

The tag deploys production directly, with no approval step. The owner's tag push is the approval. The workflow refuses to deploy unless all three checks pass, before any migration or deploy step:

- the tag matches `^v[0-9]+\.[0-9]+\.[0-9]+$`;
- `github.actor` is the owner's release account (`frankkefoueg`; until 2026-11-02 it was `KefouegFrank`, now the agents' account);
- the tagged commit is on `main` (`git merge-base --is-ancestor "$GITHUB_SHA" origin/main` after a full fetch).

Agents cannot create or push tags: the guard hook and the deny rules in `.claude/settings.json` block it, and workflow files are owner-only.

## Alternatives considered

- **Required reviewer in a `production` environment:** not available on the free plan for a private repository, and the only reviewer would be the person who just pushed the tag. Costs a paid plan (Team or Pro) for a second click by the same person.
- **Tag builds, then the owner starts the deploy by hand (`workflow_dispatch`):** buildable on the free plan, but it repeats the owner's decision in a second step and splits one release into two runs to keep in sync.
- **No checks, the tag alone:** simplest, but a mistyped tag or a tag on a non-`main` commit would reach production.

## Consequences

- One step from tag to production; a bad release is undone by a new tag or a hotfix, not by refusing an approval.
- `PROD_` secrets are repository secrets, readable by any workflow run in the repository. Two accounts have write access, both organisation owners: the owner's `frankkefoueg` and the agents' `KefouegFrank`, which the agents reach only through a fine-grained token. The GitHub-side control today is that this token has no Workflows permission, so GitHub rejects any push from it that adds or changes `.github/workflows/`; only the owner changes workflows.
- The commit-on-`main` check guards against the owner's mistakes, such as tagging the wrong commit. It does not stop someone who can edit workflows: a tag on a branch commit runs that commit's copy of the workflow, which could drop the checks. The protection there is the missing Workflows permission above.
- Confirmation: the production workflow's first job holds the three checks, and a test run with a non-owner actor or an off-`main` commit fails before deploying.
- Reconsider when the agents' token gains Workflows permission, anyone else gets write access, the repository moves to Team or Pro, or the repository becomes public: then move production secrets to a gated `production` environment with a required reviewer (paid plan) or another secret store.

## Sources

- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
