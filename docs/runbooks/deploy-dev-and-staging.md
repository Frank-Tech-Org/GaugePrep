# Deploy dev and staging

The backend deploy (Kamal) is added by its own ticket. This page covers the web placeholder on Cloudflare Pages.

## Pages publish and rollback

### Trigger

A push to `develop` publishes to `gaugeprep-dev`; a push to `stage` publishes to `gaugeprep-staging`. Each page shows the environment name and the commit it was built from.

One-time setup, by the owner:

1. Create the two projects by direct upload, with production branch `main`:

   ```bash
   CLOUDFLARE_API_TOKEN=<dev token> CLOUDFLARE_ACCOUNT_ID=<id> npx --yes wrangler@4.151.3 pages project create gaugeprep-dev --production-branch main
   CLOUDFLARE_API_TOKEN=<staging token> CLOUDFLARE_ACCOUNT_ID=<id> npx --yes wrangler@4.151.3 pages project create gaugeprep-staging --production-branch main
   ```

2. Add the four repository secrets listed in `.env.example` (`DEV_` and `STAGING_` token and account ID). Tokens: Pages edit permission only, one account.

Free plan limits: 500 builds a month and 20,000 files per site. Direct upload does not run Cloudflare builds, and the placeholder is one file.

### Steps

Republish the current head of a branch: GitHub, Actions, `pages`, Run workflow, pick `develop` or `stage`.

### Verify

```bash
curl -s https://gaugeprep-dev.pages.dev | grep -E 'id="(environment|commit)"'
curl -s https://gaugeprep-staging.pages.dev | grep -E 'id="(environment|commit)"'
```

The environment is `dev` or `staging` and the commit equals `git rev-parse origin/develop` or `origin/stage`. A publish to one environment never touches the other.

### Rollback

Cloudflare dashboard, Workers & Pages, the project, Deployments: open the previous good deployment, then Rollback to this deployment (production deployments only). Run the verify curl; it shows the earlier commit. The next push publishes a new deployment over it, so to keep the rollback revert the commit on the branch.
