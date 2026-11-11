# Deploy dev and staging

Two parts: the backend on the shared server with Kamal, then the web placeholder on Cloudflare Pages.

## Backend deploy with Kamal

Dev and staging run on one server (an AWS t4g.small in Stockholm) behind one kamal-proxy. They run the same image, `ghcr.io/frank-tech-org/gaugeprep-backend`, tagged with the git sha: dev builds it, staging deploys that same version, so what reaches staging is what was tested on dev, and a rollback is a version that already exists.

|                   | Dev                               | Staging                               |
| ----------------- | --------------------------------- | ------------------------------------- |
| Host              | `dev.gaugeprep.com`               | `staging.gaugeprep.com`               |
| Kamal destination | `-d dev`                          | `-d staging`                          |
| Doppler config    | `gaugeprep/dev`                   | `gaugeprep/stg`                       |
| Containers        | `gaugeprep-backend-web-dev-<sha>` | `gaugeprep-backend-web-staging-<sha>` |

Config is in `infra/kamal/`. Each destination's secrets file in `.kamal/` fetches its own keys from its own Doppler config, so a staging deploy can never pick up dev's database or key. Each web container is capped at 320 MB and the proxy at 64 MB. Run every command from the repo root.

### Trigger

A version needs to reach dev or staging, or the last deploy broke one and the previous version must come back. Both hold synthetic data only.

### One-time setup

1. `doppler login`, and check `doppler secrets --project gaugeprep --config stg --only-names` lists `DATABASE_URL`, `DJANGO_SECRET_KEY`, `KAMAL_REGISTRY_USERNAME`, `KAMAL_REGISTRY_PASSWORD` and `SERVER_HOST` (and the same for `dev`). New values go in with `doppler secrets set KEY --project gaugeprep --config <dev|stg>`, which prompts instead of taking the value on the command line.
2. Kamal 2.12.0 and arm64 emulation, since an x86 machine builds arm64 images:

   ```bash
   sudo apt-get install -y ruby-full build-essential
   sudo gem install kamal -v 2.12.0
   docker run --privileged --rm tonistiigi/binfmt --install arm64
   ```

3. The deploy key: `ssh-add ~/.ssh/gaugeprep-deploy`, then `ssh deploy@dev.gaugeprep.com docker ps` must work.
4. A new server only: rebuild it with `staging-rebuild.md`, then `kamal setup -c infra/kamal/deploy.yml -d dev` once, which logs the server into the registry and starts kamal-proxy. Never run `setup` once the proxy runs: it restarts the proxy and cuts both environments off.

### Steps

Deploy dev from the committed head (Kamal builds from git, so commit first):

```bash
time kamal deploy -c infra/kamal/deploy.yml -d dev
```

Promote the version on dev to staging without rebuilding:

```bash
kamal deploy -c infra/kamal/deploy.yml -d staging --skip-push --version <sha on dev>
```

The new container runs `migrate`, then gunicorn. Traffic moves once `/api/v1/health` passes, within the 60 s `deploy_timeout` in `deploy.yml`, which covers migrations too; raise it before a slow one. If `migrate` fails, the container never goes healthy and the old version keeps serving.

The server allows 5 new SSH connections per 30 s. Wait 30 s between Kamal commands and never run two at once.

### Verify

```bash
curl -s https://staging.gaugeprep.com/api/v1/health                # {"status":"ok","database":"ok"}
curl -sv -o /dev/null https://staging.gaugeprep.com/api/v1/health 2>&1 | grep -E "issuer|HTTP/2 "
kamal app details -c infra/kamal/deploy.yml -d staging             # up, on the sha
```

To show a deploy had no gap, run this in a second terminal while it deploys, against both hosts; it must print only 200:

```bash
while true; do curl -s -o /dev/null -w '%{http_code}\n' https://staging.gaugeprep.com/api/v1/health; sleep 0.5; done
```

On the server (`ssh deploy@dev.gaugeprep.com`):

```bash
free -m                         # used under 1,100 with both idle
docker stats --no-stream        # every container under its limit
sudo ss -ltnp                   # only kamal-proxy on 80 and 443, sshd on 22
sudo dmesg | grep -i oom || echo "no oom"
```

### Rollback

```bash
kamal app containers -c infra/kamal/deploy.yml -d staging
kamal rollback <earlier sha> -c infra/kamal/deploy.yml -d staging
```

Kamal keeps the last 3 versions of each environment on the server, and every version stays in the registry. A rollback does not undo migrations; they are expand-then-contract, so older code runs on the newer schema. The next deploy moves forward again.

### Failing migration

To check the safety net, deploy a scratch commit whose migration raises:

```bash
git switch -c scratch/failing-migration
mkdir -p backend/modules/learner/migrations && touch backend/modules/learner/migrations/__init__.py
printf 'from django.db import migrations\n\n\ndef boom(apps, schema_editor):\n    raise RuntimeError("deliberate failure")\n\n\nclass Migration(migrations.Migration):\n    dependencies = []\n    operations = [migrations.RunPython(boom)]\n' > backend/modules/learner/migrations/0001_fail.py
git add backend && git commit -m "test(api): failing migration" --no-verify
kamal deploy -c infra/kamal/deploy.yml -d staging
git switch - && git branch -D scratch/failing-migration
```

The deploy exits non-zero, staging still answers 200 on the previous version, and the migration's transaction leaves nothing to undo.

### Warning

One kamal-proxy serves both environments. Rebooting the server, or `kamal proxy reboot` or `kamal setup` from either destination, interrupts dev and staging together.

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

2. Add four repository secrets, `DEV_CLOUDFLARE_API_TOKEN`, `DEV_CLOUDFLARE_ACCOUNT_ID` and the two `STAGING_` ones, with the values from Doppler (`CLOUDFLARE_*` in `gaugeprep/dev` and `gaugeprep/stg`). Tokens: Pages edit permission only. That permission covers every Pages project in the account, so keep production in a different Cloudflare account.

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
