# Deploy dev and staging

Purpose: put a backend version or the web placeholder on dev or staging, check it and roll it back. Run every command from the repo root.

| | Dev | Staging |
|---|---|---|
| API host | `api.dev.gaugeprep.com` | `api.staging.gaugeprep.com` |
| Kamal destination | `-d dev` | `-d staging` |
| Doppler config | `gaugeprep/dev` | `gaugeprep/stg` |

## Manual backend deploy

### Trigger

A version must reach dev or staging by hand, or a deploy broke one and the previous version must come back.

### Prerequisites

- [ ] Doppler logged in as you, `DOPPLER_TOKEN` unset: `doppler secrets --project gaugeprep --config stg --only-names` lists `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `DJANGO_SECRET_KEY`, `KAMAL_REGISTRY_USERNAME`, `KAMAL_REGISTRY_PASSWORD`, `SERVER_HOST`, `SERVER_HOST_KEY`, `SSH_PRIVATE_KEY`, `SSH_PUBLIC_KEY` (same for `dev`). Add a missing one with `doppler secrets set KEY --project gaugeprep --config <dev|stg>`.
- [ ] Kamal 2.12.0 and arm64 emulation: `sudo apt-get install -y ruby-full build-essential && sudo gem install kamal -v 2.12.0 && docker run --privileged --rm tonistiigi/binfmt --install arm64`
- [ ] Deploy key loaded: `ssh-add ~/.ssh/gaugeprep-deploy`, then `ssh deploy@<server ip> docker ps` works.
- [ ] New server only: rebuilt with the server rebuild runbook, then `kamal setup -c infra/kamal/deploy.yml -d dev` run once. Never run `setup` again once the proxy runs: it cuts off both environments.
- [ ] Your change is committed (Kamal builds from git). Wait 30 s between Kamal commands and never run two at once (the server allows 5 new SSH connections per 30 s).

### Steps

1. Deploy dev: `kamal deploy -c infra/kamal/deploy.yml -d dev`. Expect: exit 0; the new container migrated and took traffic after `/api/v1/health` passed.
2. Promote that version to staging: `kamal deploy -c infra/kamal/deploy.yml -d staging --skip-push --version <sha on dev>`. Expect: exit 0. A failed migration exits non-zero and the old version keeps serving.

### Verify

1. `curl -s https://api.staging.gaugeprep.com/api/v1/health`. Pass: `{"status":"ok","database":"ok"}`.
2. `curl -sv -o /dev/null https://api.staging.gaugeprep.com/api/v1/health 2>&1 | grep -E "issuer|HTTP/2 "`. Pass: a valid issuer and `HTTP/2 200`.
3. `kamal app details -c infra/kamal/deploy.yml -d staging`. Pass: up, on the sha.
4. No gap, in a second terminal during a deploy: `while true; do curl -s -o /dev/null -w '%{http_code}\n' https://api.staging.gaugeprep.com/api/v1/health; sleep 0.5; done`. Pass: only 200.
5. On the server (`ssh deploy@<server ip>`): `free -m` used under 1,100; `docker stats --no-stream` every container under its limit; `ss -ltnH | awk '{print $4}'` public only 22, 80, 443; `docker inspect kamal-proxy --format '{{json .HostConfig.PortBindings}}'` 80 and 443 on the proxy; `journalctl -k -q | grep -ciE 'out of memory|oom-kill'` prints 0.
6. Optional, failing migration: on `git switch -c scratch/failing-migration`, add a migration in `apps/backend/modules/learner/migrations/0001_fail.py` whose `RunPython` raises, commit with `--no-verify`, run `kamal deploy -c infra/kamal/deploy.yml -d staging`, then `git switch - && git branch -D scratch/failing-migration`. Pass: the deploy exits non-zero and staging still answers 200.

### Rollback

1. List versions: `kamal app containers -c infra/kamal/deploy.yml -d staging`.
2. Roll back: `kamal rollback <earlier sha> -c infra/kamal/deploy.yml -d staging`. If the sha is no longer on the server, `kamal deploy -c infra/kamal/deploy.yml -d staging --skip-push --version <sha>` pulls it from the registry.
3. Run Verify 1 and 3. Migrations stay applied; they are expand-then-contract, so older code runs on the newer schema.

## Database roles

### Trigger

First setup of an environment, or a password rotation. Steps shown for dev; the role model is in the data model spec.

### Prerequisites

- [ ] `$OWNER_URL` is the Neon owner URL for the branch without password (`postgresql://<owner>@<host>/<db>?sslmode=require`).

### Steps

1. Load the owner password: `read -rs PGPASSWORD; export PGPASSWORD`. Expect: no echo.
2. Create the roles: `psql "$OWNER_URL" -c 'CREATE ROLE gaugeprep_dev_migrator LOGIN' -c 'CREATE ROLE gaugeprep_dev_app LOGIN'`. Expect: `CREATE ROLE` twice.
3. Set passwords: `psql "$OWNER_URL" -c '\password gaugeprep_dev_migrator'`, then the same for `gaugeprep_dev_app`. Expect: prompt, no error.
4. Grant: `(cd apps/backend && uv run python -m config.db_roles gaugeprep_dev_migrator gaugeprep_dev_app) | psql "$OWNER_URL" -v ON_ERROR_STOP=1`. Expect: exit 0. It stops if a table is not owned by the migration role.
5. Store the URLs: `doppler secrets set DATABASE_URL --project gaugeprep --config dev` (serving role) and `MIGRATION_DATABASE_URL` (migration role), then `unset PGPASSWORD`.
6. Deploy dev (Manual backend deploy, step 1). On a rebuilt database, rerun step 4 after this first deploy.
7. To rotate: `\password <role>` as owner, update that role's Doppler key, redeploy; one role at a time.

### Verify

With `$APP_URL` the serving role's URL and its password in `PGPASSWORD`:

1. `psql "$APP_URL" -c 'CREATE TABLE t (i int)'`. Pass: permission denied.
2. `psql "$APP_URL" -c 'ALTER TABLE django_migrations ADD COLUMN x int'`. Pass: must be owner.
3. `psql "$APP_URL" -c 'SELECT count(*) FROM procrastinate_jobs'`. Pass: a count.
4. `curl -s https://api.dev.gaugeprep.com/api/v1/health`. Pass: `{"status":"ok","database":"ok"}`. Then `unset PGPASSWORD`.

### Rollback

1. Set `DATABASE_URL` in Doppler back to the migration role's URL.
2. Redeploy. The app runs as owner again; step 4 can be rerun at any time.

## Automatic backend deploy

### Trigger

A push to `develop` deploys dev (`deploy-dev`); a push to `stage` deploys staging (`deploy-staging`), which waits for the owner's approval. What the workflow runs is in the CI doc.

### Prerequisites

- [ ] Environment secret `DOPPLER_TOKEN` in `dev` and `staging`, read-only, under 90 days old.
- [ ] Package `gaugeprep-backend`, Package settings, Manage Actions access: this repository has Write (else the push fails with `denied`).

### Steps

1. Approve staging: open the run, Review deployments, Approve. Expect: the deploy job starts.
2. Rerun: Actions, the newest run, Re-run failed jobs. Deploy staging by hand: Actions, `deploy-staging`, Run workflow, pick `stage` or `hotfix/*`, approve.
3. Stale lock after a dead run: `kamal lock release -c infra/kamal/deploy.yml -d <dev|staging>`. Expect: lock released.
4. Rotate the Doppler token every 90 days: `doppler configs tokens create ci-deploy --project gaugeprep --config <deploy_dev|deploy_stg> --max-age 2160h --plain | gh secret set DOPPLER_TOKEN --env <dev|staging>`, then `doppler configs tokens revoke --slug <slug>`.
5. Rotate the CI SSH key: new ed25519 pair, `doppler secrets set SSH_PRIVATE_KEY` and `SSH_PUBLIC_KEY` in `dev` or `stg`, append the public key to the deploy user's `~/.ssh/authorized_keys`, remove the old line.
6. After a server rebuild: `doppler secrets get SSH_PUBLIC_KEY --plain -p gaugeprep -c <dev|stg> | ssh deploy@<server ip> 'cat >> ~/.ssh/authorized_keys'` for both, and refresh `SERVER_HOST_KEY` in both from `ssh-keyscan -t ed25519 <server ip>`.

### Verify

1. `curl -s https://api.dev.gaugeprep.com/api/v1/health`. Pass: `{"status":"ok","database":"ok"}`.
2. `kamal app details -c infra/kamal/deploy.yml -d dev`. Pass: up, on the run's sha.
3. `gh run list --workflow deploy-dev.yml`. Pass: duration under 15 minutes.

### Rollback

1. `kamal rollback <earlier sha> -c infra/kamal/deploy.yml -d <dev|staging>`, or revert the commit and let the push deploy it.
2. To pause automatic deploys, disable the workflow in Actions; manual deploys keep working.

## Pages publish

### Trigger

A push to `develop` publishes `gaugeprep-dev`, a push to `stage` publishes `gaugeprep-staging`, after the PR checks pass.

### Prerequisites

- [ ] Projects exist. If not, with the dev token: `read -rs CLOUDFLARE_API_TOKEN; export CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID=<id> npx --yes wrangler@4.153.0 pages project create gaugeprep-dev --production-branch main`; repeat with the staging token for `gaugeprep-staging`; `unset CLOUDFLARE_API_TOKEN`. If wrangler opens a browser, the token was not read: check the account, then `npx --yes wrangler@4.153.0 logout`.
- [ ] Repository secrets `DEV_CLOUDFLARE_API_TOKEN`, `DEV_CLOUDFLARE_ACCOUNT_ID` and the two `STAGING_` ones, values from Doppler, tokens with Pages edit only.

### Steps

1. Republish: Actions, `pages`, Run workflow, pick `develop` or `stage`. Expect: `checks` green, then publish.
2. A red check: open the run, fix on the branch, or Re-run failed jobs for a flaky one.

### Verify

1. `curl -s https://gaugeprep-dev.pages.dev | grep -E 'id="(environment|commit)"'`, and the same for `gaugeprep-staging`. Pass: environment `dev` or `staging`, commit equal to `git rev-parse origin/develop` or `origin/stage`.

### Rollback

1. Cloudflare dashboard, Workers & Pages, the project, Deployments, the previous good one, Rollback to this deployment.
2. Run Verify 1. Pass: the earlier commit.
3. Revert the commit on the branch, or the next push publishes over the rollback.

## Worker and mail

### Trigger

First deploy of the worker, a worker password rotation, or a mail check after a deploy.

### Prerequisites

- [ ] Doppler holds `WORKER_DATABASE_URL` and `MAIL_HEALTH_TO` in `dev` and `stg`, plus `MAIL_API_KEY` in `stg`.
- [ ] Staging only: the Resend sending domain `mail.staging.gaugeprep.com` is verified and `MAIL_HEALTH_TO` is the test inbox.

### Steps

1. Create or rotate the worker role: `infra/server/worker-role.sh dev` (then `stg`). Expect: `worker role ... ready`. Run it again after any deploy that adds job tables.
2. Deploy: `kamal deploy -c infra/kamal/deploy.yml -d dev`. Expect: exit 0, a `worker` container beside `web`.
3. First time on dev only: `kamal accessory boot mailpit -c infra/kamal/deploy.yml -d dev`. Expect: Mailpit running.
4. Send the health job: `kamal app exec -r web -c infra/kamal/deploy.yml -d dev "python manage.py procrastinate defer mail_health"`. Expect: `Deployed 1 job`.

### Verify

1. `kamal app logs -r worker -c infra/kamal/deploy.yml -d dev --lines 20`. Pass: `job_started`, `mail_sent template=health`, `job_succeeded`.
2. Dev: `ssh -L 8025:127.0.0.1:8025 deploy@<server ip>`, open `http://localhost:8025`. Pass: the message is listed.
3. Staging: open the test inbox, show the original message. Pass: SPF and DKIM `pass`.
4. As the worker role: `psql "$WORKER_URL" -c 'SELECT 1 FROM django_migrations'`. Pass: permission denied.

### Rollback

1. Dev: `kamal app stop -r worker -c infra/kamal/deploy.yml -d dev`; queued jobs wait in the database.
2. Roll the app back as in Manual backend deploy. A job killed mid-run is requeued within a minute of the next worker start.
