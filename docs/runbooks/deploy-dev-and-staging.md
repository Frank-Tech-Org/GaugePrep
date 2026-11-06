# Deploy dev and staging

The backend deploy (Kamal) is added by its own ticket. This page covers the web placeholder on Cloudflare Pages.

## Pages publish and rollback

### Trigger

A push to `develop` publishes to `gaugeprep-dev`; a push to `stage` publishes to `gaugeprep-staging`. Each page shows the environment name and the commit it was built from.

The publish waits for the same checks a pull request runs (the `checks` job in the `pages` run). If any check fails, nothing is published and the page keeps its previous commit. To see which check failed: GitHub, Actions, the `pages` run, `checks`; the red job is named after the check (`checks / gate`, `checks / check`, `checks / semgrep`, `checks / trivy`, and so on). On a push the pull-request-only checks are skipped: PR title and description, scanner settings and changed-lines coverage. Every code check runs, even for a docs-only push.

One-time setup, by the owner:

1. Create the two projects by direct upload, with production branch `main`:

   ```bash
   read -rs CLOUDFLARE_API_TOKEN; export CLOUDFLARE_API_TOKEN   # paste the dev token; keeps it out of shell history
   CLOUDFLARE_ACCOUNT_ID=<id> npx --yes wrangler@4.153.0 pages project create gaugeprep-dev --production-branch main
   read -rs CLOUDFLARE_API_TOKEN; export CLOUDFLARE_API_TOKEN   # now the staging token
   CLOUDFLARE_ACCOUNT_ID=<id> npx --yes wrangler@4.153.0 pages project create gaugeprep-staging --production-branch main
   unset CLOUDFLARE_API_TOKEN
   ```

   If wrangler opens a browser login instead of using the pasted token, it did not read the token (empty paste, or not exported). The project is then created under whichever account you log in with, so check it is in the intended account, and run `npx --yes wrangler@4.153.0 logout` afterwards. Run the setup from a directory that exists: npx fails with `ENOENT uv_cwd` from a deleted one.

2. Add the four repository secrets listed in `.env.example` (`DEV_` and `STAGING_` token and account ID). Tokens: Pages edit permission only. That permission covers every Pages project in the account, so keep production in a different Cloudflare account.

The secrets are repository-wide: anyone who can push a branch can write a workflow that reads them. The `if` on the branch in the workflow is not a barrier against that. Keep write access to trusted people only; GitHub Environments with a branch rule would close it, if the plan allows them for a private repository.

Free plan limits: 500 builds a month and 20,000 files per site. Direct upload does not run Cloudflare builds, and the placeholder is one file.

### Steps

Republish the current head of a branch: GitHub, Actions, `pages`, Run workflow, pick `develop` or `stage`.

A manual run waits for the checks too. If a run stopped on a failing check, fix it on the branch (a new push publishes) or, for a flaky check, open the run and Re-run failed jobs: the publish job then runs once the check is green. When two pushes land close together, the older run skips its publish with a notice ("develop has moved on") and the newer run publishes.

Staging only publishes once the workflow exists on `stage`, so the first staging publish needs a `develop` to `stage` promotion. Running the workflow from `develop` skips the staging job, which runs only on the `stage` ref; to republish staging, choose `stage` in Run workflow.

### Verify

```bash
curl -s https://gaugeprep-dev.pages.dev | grep -E 'id="(environment|commit)"'
curl -s https://gaugeprep-staging.pages.dev | grep -E 'id="(environment|commit)"'
```

The environment is `dev` or `staging` and the commit equals `git rev-parse origin/develop` or `origin/stage`. A publish to one environment never touches the other.

### Rollback

Cloudflare dashboard, Workers & Pages, the project, Deployments: open the previous good deployment, then Rollback to this deployment (production deployments only). Run the verify curl; it shows the earlier commit. The next push publishes a new deployment over it, so to keep the rollback revert the commit on the branch. To see a rollback work, the previous deployment must have a different commit from the current one. A rollback is undone by the next publish.

To undo the gate itself (the checks keep blocking publishes and the cause cannot be fixed quickly), revert the commit that added it on `develop`, then promote to `stage`; the publish goes back to running without the checks.
