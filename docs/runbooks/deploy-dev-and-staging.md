# Deploy dev and staging

Two parts: the backend on the shared server with Kamal (dev, then staging on the same machine), then the web placeholder on Cloudflare Pages.

## Backend deploy with Kamal (dev)

Config is in `infra/kamal/`: `deploy.yml` (shared) and `deploy.dev.yml` (dev); the secrets files are `.kamal/secrets-common` and `.kamal/secrets.dev` (they only read your shell, no values). Run every Kamal command from the repo root. Dev is `dev.gaugeprep.com` (a DNS-only A record in Cloudflare pointing at the server), image `ghcr.io/frank-tech-org/gaugeprep-backend`, containers named `gaugeprep-backend-dev-web-...`.

### Trigger

You want a version of the backend on dev, or the last deploy broke it and you want the previous one back. Dev holds synthetic data only.

### One-time setup

1. Rebuild or check the server with `docs/runbooks/staging-rebuild.md` (it adds the swapfile). `ssh deploy@$DEV_SERVER_HOST docker ps` must work with your deploy key.
2. Install Kamal and register QEMU once, since an x86 machine builds arm64 under emulation:

   ```bash
   sudo apt-get install -y ruby-full build-essential
   sudo gem install kamal -v 2.12.0
   docker run --privileged --rm tonistiigi/binfmt --install arm64
   ```

3. Create a GitHub personal access token (classic) from https://github.com/settings/tokens/new?scopes=write:packages, with an expiry; GitHub ticks `repo` too if you start from a blank form, and the token sits in plain text on the server. Create a Neon branch for dev and use its direct connection string (pooling off), since migrations run through it. Export the five keys in the shell you deploy from (`.env.example` says where each comes from; `read -rs` keeps values out of shell history):

   ```bash
   export KAMAL_REGISTRY_USERNAME=<your GitHub user name>
   read -rs KAMAL_REGISTRY_PASSWORD; export KAMAL_REGISTRY_PASSWORD   # the GitHub token
   read -rs DEV_DATABASE_URL; export DEV_DATABASE_URL                 # Neon dev branch connection string
   read -rs DEV_DJANGO_SECRET_KEY; export DEV_DJANGO_SECRET_KEY       # python -c "import secrets; print(secrets.token_urlsafe(50))"
   export DEV_SERVER_HOST=<server address>
   ```

   If the values are already in `.env`, load just these keys and the deploy key instead:

   ```bash
   while IFS= read -r l; do export "$l"; done < <(grep -E '^(DEV_[A-Z_]+|KAMAL_REGISTRY_[A-Z_]+)=' .env)
   eval "$(ssh-agent -s)" && ssh-add ~/.ssh/gaugeprep-deploy
   ```

   Then check the token's scopes; it must list only `write:packages` (and `read:packages`). The token goes through stdin so it never shows in the process list:

   ```bash
   printf 'Authorization: token %s\n' "$KAMAL_REGISTRY_PASSWORD" | curl -sI -H @- https://api.github.com/user | grep -i x-oauth-scopes
   ```

4. Confirm the config reads (no server contact): `cd <repo root> && kamal config -c infra/kamal/deploy.yml -d dev`.
5. The first time on a new server, run `kamal setup -c infra/kamal/deploy.yml -d dev` instead of `kamal deploy`: it logs the server into the registry and boots kamal-proxy before the first deploy.

### Steps

Deploy the committed head of the branch you are on. Kamal builds from git, so commit first.

```bash
cd <repo root>
time kamal deploy -c infra/kamal/deploy.yml -d dev
```

That builds the arm64 `production` image, pushes it, starts the new container, which runs `migrate` before gunicorn, waits for `/api/v1/health` and only then moves traffic. If `migrate` fails, the container exits, health never passes and the old version keeps serving. Kamal waits 60 s for health (`deploy_timeout` in `deploy.yml`), migrations included; raise it before deploying a migration that takes longer. The first run also boots kamal-proxy (64 MB) and requests the certificate, so the DNS record must resolve and ports 80 and 443 must be open. The first build is uncached; run it again after a small change for the cached time, and note both in the PR with "QEMU" or "native".

Redeploy: run the same command. If the version is unchanged Kamal reuses the pushed image and swaps the container behind the proxy. To watch for gaps, run this in a second terminal while it deploys; it must print only 200:

```bash
while true; do curl -s -o /dev/null -w '%{http_code}\n' https://dev.gaugeprep.com/api/v1/health; sleep 0.5; done
```

### Verify

From your machine:

```bash
cd <repo root>
curl -s https://dev.gaugeprep.com/api/v1/health
curl -sv -o /dev/null https://dev.gaugeprep.com/api/v1/health 2>&1 | grep -E "issuer|HTTP/2 "
kamal app details -c infra/kamal/deploy.yml -d dev
docker pull ghcr.io/frank-tech-org/gaugeprep-backend:$(git rev-parse HEAD)
docker image inspect ghcr.io/frank-tech-org/gaugeprep-backend:$(git rev-parse HEAD) --format '{{range .Config.Env}}{{println .}}{{end}}' | grep DJANGO_SETTINGS_MODULE
```

Expect `{"status":"ok","database":"ok"}`, an issuer of Let's Encrypt with `HTTP/2 200` (curl stops on a bad certificate; the endpoint answers GET only, so `-I` gets 405), the container up with the git sha as version, and `DJANGO_SETTINGS_MODULE=config.settings.production`.

On the server (`ssh deploy@$DEV_SERVER_HOST`):

```bash
sudo ss -ltnp
free -m
docker stats --no-stream
swapon --show
docker inspect $(docker ps -q --filter name=gaugeprep-backend-dev-web) --format '{{.HostConfig.Memory}}'
sudo ufw status verbose
```

Expect: nothing on `0.0.0.0` or `[::]` except kamal-proxy on 80 and 443 (and sshd on 22, which ufw limits); `used` under 900 in `free -m`; every container under its limit (web 320 MiB, proxy 64 MiB); `/swapfile` at 2G; `335544320` (320 MiB) for the web container, which `kamal app details` does not print; `22/tcp LIMIT IN`, 80 and 443 `ALLOW IN`.

SSH limit (5 new connections per 30 s), from your machine:

```bash
for i in $(seq 1 8); do ssh -o ConnectTimeout=5 -o BatchMode=yes deploy@$DEV_SERVER_HOST true && echo "$i ok" || echo "$i refused"; done
```

The first 5 inside 30 s connect and the rest are refused until the window passes. Wait 30 s before deploying again.

### Failing migration

The deploy must stop before the switch. On a scratch branch add a migration that raises, deploy, then drop the branch:

```bash
cd <repo root>
git switch -c scratch/failing-migration
mkdir -p backend/modules/learner/migrations
touch backend/modules/learner/migrations/__init__.py
printf 'from django.db import migrations\n\n\ndef boom(apps, schema_editor):\n    raise RuntimeError("deliberate failure")\n\n\nclass Migration(migrations.Migration):\n    dependencies = []\n    operations = [migrations.RunPython(boom)]\n' > backend/modules/learner/migrations/0001_fail.py
git add backend && git commit -m "test(api): failing migration"
kamal deploy -c infra/kamal/deploy.yml -d dev
curl -s https://dev.gaugeprep.com/api/v1/health
git switch - && git branch -D scratch/failing-migration
```

`kamal deploy` exits non-zero because the new container never becomes healthy, the health call still returns 200 from the previous version, and `kamal app details` shows the old version. The migration runs in a transaction, so the database has nothing to undo.

### Rollback

To the previous version (Kamal keeps the last 3 containers and the images are in the registry):

```bash
cd <repo root>
kamal app containers -c infra/kamal/deploy.yml -d dev
kamal rollback <previous version from that list> -c infra/kamal/deploy.yml -d dev
curl -s https://dev.gaugeprep.com/api/v1/health
kamal app details -c infra/kamal/deploy.yml -d dev
```

The health call returns 200 and the details show the earlier version. A rollback does not undo migrations; they are expand-then-contract, so the older code runs on the newer schema, and anything else is fixed forward with a new deploy. The next `kamal deploy` moves dev to the branch head again.

If kamal-proxy is stuck: `kamal proxy reboot -c infra/kamal/deploy.yml -d dev` (a few seconds of downtime for everything behind it).

### Notes

- Only kamal-proxy publishes ports (80 and 443). The web container publishes none: the proxy reaches it over the Docker network on 8000. A future accessory must publish on `127.0.0.1` only, because Docker-published ports bypass ufw.
- No worker role yet; it comes with the first background task.
- Staging shares `deploy.yml` and `.kamal/secrets-common` with dev, and has its own destination file, secrets file, image name and host. See the next section.

## Backend deploy with Kamal (staging)

Staging runs on the same server as dev, behind the same kamal-proxy. Files: `infra/kamal/deploy.staging.yml` and `.kamal/secrets.staging`, which reads only `STAGING_DATABASE_URL` and `STAGING_DJANGO_SECRET_KEY`. The host is `staging.gaugeprep.com` (a DNS-only A record to the server), the service is `gaugeprep-backend-staging`, containers are `gaugeprep-backend-staging-web-...`, and the web container is capped at 320 MB like dev.

The image is `ghcr.io/frank-tech-org/gaugeprep-backend-staging`, set only in the staging destination. With one name, a dev and a staging build of the same commit would push the same tag, the second would overwrite the first's service label, and a later dev redeploy or rollback to that commit would fail.

### Trigger

A release candidate needs checking, the owner wants the Friday demo, or the last staging deploy broke it. Staging holds synthetic data only.

### Setup

Same Kamal, QEMU, registry token and deploy key as the dev setup above. Export the staging keys in the shell you deploy from (`read -rs` keeps values out of shell history):

```bash
read -rs STAGING_DATABASE_URL; export STAGING_DATABASE_URL                 # Neon staging branch, direct connection (pooling off)
read -rs STAGING_DJANGO_SECRET_KEY; export STAGING_DJANGO_SECRET_KEY       # a different key from dev's
export STAGING_SERVER_HOST=staging.gaugeprep.com
kamal config -c infra/kamal/deploy.yml -d staging                          # no server contact
```

Never run `kamal setup` for staging. The proxy already runs for dev, and setup would reboot it and cut dev off. Staging is always `kamal deploy`.

### Steps

Kamal builds from git, so commit first. Deploy the head of the branch you are on:

```bash
cd <repo root>
time kamal deploy -c infra/kamal/deploy.yml -d staging
```

The new container runs `migrate` before gunicorn, and traffic moves only once `/api/v1/health` passes, inside the 60 s `deploy_timeout`. If `migrate` fails the container never goes healthy and the old version keeps serving. The first deploy also gets the Let's Encrypt certificate through the proxy, so the DNS record must already resolve.

Redeploy: run the same command. In a second terminal, this must print only 200 while it runs:

```bash
while true; do curl -s -o /dev/null -w '%{http_code}\n' https://staging.gaugeprep.com/api/v1/health; sleep 0.5; done
```

The server allows 5 new SSH connections per 30 s. Wait 30 s between Kamal commands that open many connections (deploy, rollback, `app details`, `app containers`), and never run two at once.

### Verify

```bash
cd <repo root>
curl -s https://staging.gaugeprep.com/api/v1/health
curl -vI https://staging.gaugeprep.com 2>&1 | grep -E "issuer|subject"
kamal app details -c infra/kamal/deploy.yml -d staging
```

Expect `{"status":"ok","database":"ok"}`, a Let's Encrypt issuer (`-I` gets 405 on the health path, which doesn't matter for the certificate) and the container up on the git sha. On the server (`ssh deploy@$STAGING_SERVER_HOST`):

```bash
free -m
docker stats --no-stream
sudo ss -ltnp
docker inspect $(docker ps -q --filter name=gaugeprep-backend-staging-web) --format '{{.HostConfig.Memory}}'
sudo dmesg | grep -i -E "out of memory|oom" || echo "no oom"
```

Expect `used` under 1,100 MB with both environments idle, every container under its limit, only kamal-proxy on 80 and 443 (plus sshd on 22), `335544320` for the staging web container and no OOM lines. Sample `free -m` again in the middle of a deploy, when three web containers run.

Check dev is untouched, after every staging deploy or rollback, and the other way round after a dev deploy:

```bash
curl -s https://dev.gaugeprep.com/api/v1/health
kamal app details -c infra/kamal/deploy.yml -d dev
```

Dev must answer 200 on the same version as before. Run the 200-loop against dev during the staging deploy to show it never dropped.

### Failing migration

Same procedure as dev, with `-d staging` and the staging host. The deploy exits non-zero, the staging health call still returns 200 from the previous version, and `kamal app details` shows the old version.

### Rollback

```bash
cd <repo root>
kamal app containers -c infra/kamal/deploy.yml -d staging
kamal rollback <previous version from that list> -c infra/kamal/deploy.yml -d staging
curl -s https://staging.gaugeprep.com/api/v1/health
curl -s https://dev.gaugeprep.com/api/v1/health
kamal app details -c infra/kamal/deploy.yml -d staging
```

Staging answers 200 on the earlier version and dev keeps answering 200. Migrations are not undone (expand-then-contract). With the same commit on both environments, a dev rollback still works because it pulls `gaugeprep-backend`, never the staging image.

### Warning

One kamal-proxy serves both environments. Rebooting the server, or running `kamal proxy reboot` or `kamal setup` from either destination, interrupts dev and staging together.

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
