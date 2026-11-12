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

1. `doppler login`, and check `doppler secrets --project gaugeprep --config stg --only-names` lists `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `DJANGO_SECRET_KEY`, `KAMAL_REGISTRY_USERNAME`, `KAMAL_REGISTRY_PASSWORD` and `SERVER_HOST` (and the same for `dev`). New values go in with `doppler secrets set KEY --project gaugeprep --config <dev|stg>`, which prompts instead of taking the value on the command line. Deploy as your logged-in Doppler user with `DOPPLER_TOKEN` unset: with a service token Kamal ignores the config named in the secrets file, so the Kamal config refuses to load. If `kamal` fails with `servers/web/hosts/0: should be a string or a hash`, Doppler is logged out or `SERVER_HOST` is missing.
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

On the server (`ssh deploy@dev.gaugeprep.com`; the deploy user has no sudo):

```bash
free -m                         # used under 1,100 with both idle
docker stats --no-stream        # every container under its limit
ss -ltnH | awk '{print $4}'     # public: only 22, 80 and 443; the rest on 127.0.0.x
docker inspect kamal-proxy --format '{{json .HostConfig.PortBindings}}'   # 80 and 443 are the proxy's
journalctl -k -q | grep -ciE 'out of memory|oom-kill'                     # 0
```

### Rollback

```bash
kamal app containers -c infra/kamal/deploy.yml -d staging
kamal rollback <earlier sha> -c infra/kamal/deploy.yml -d staging
```

The server keeps the last 10 stopped containers of both environments together, so a run of dev deploys can push out staging's previous version. Every version stays in the registry, so any of them comes back with `kamal deploy -c infra/kamal/deploy.yml -d staging --skip-push --version <sha>`. A rollback does not undo migrations; they are expand-then-contract, so older code runs on the newer schema. The next deploy moves forward again.

### Failing migration

To check the safety net, deploy a scratch commit whose migration raises:

```bash
git switch -c scratch/failing-migration
mkdir -p apps/backend/modules/learner/migrations && touch apps/backend/modules/learner/migrations/__init__.py
printf 'from django.db import migrations\n\n\ndef boom(apps, schema_editor):\n    raise RuntimeError("deliberate failure")\n\n\nclass Migration(migrations.Migration):\n    dependencies = []\n    operations = [migrations.RunPython(boom)]\n' > apps/backend/modules/learner/migrations/0001_fail.py
git add backend && git commit -m "test(api): failing migration" --no-verify
kamal deploy -c infra/kamal/deploy.yml -d staging
git switch - && git branch -D scratch/failing-migration
```

The deploy exits non-zero, staging still answers 200 on the previous version, and the migration's transaction leaves nothing to undo.

### Database roles

Each database has two roles. The migration role owns the schemas and tables and is the only one that can change them; its URL is `MIGRATION_DATABASE_URL`, used only by the migrate step at container start (gunicorn starts without it). The key is hosted only (Doppler `dev` and `stg`); local runs use `DATABASE_URL` for both. The serving role is the app's `DATABASE_URL`: select, insert, update and delete on ordinary tables, select and insert only on append-only ones, select only on `django_migrations` (the app only reads it at startup), no right to create, alter or drop anything. A migration makes a table append-only with `append_only("<schema>.<table>")` from `config.append_only`; it adds triggers that refuse update, delete and truncate, and the role SQL recognises such tables by that trigger. Because the triggers also stop the migration role, Django's flush (tests with `transaction=True`) fails on those tables, and a data fix that updates their rows must reverse the operation, run the fix and apply it again. Neon roles are shared by every branch of a project, so dev and staging each get a pair: `gaugeprep_dev_migrator` and `gaugeprep_dev_app`, `gaugeprep_stg_migrator` and `gaugeprep_stg_app`.

Trigger: first setup of an environment, or a password rotation.

Steps, per environment (shown for dev). `$OWNER_URL` is the Neon owner's URL for that branch without the password (`postgresql://<owner>@<host>/<db>?sslmode=require`); the password goes in `PGPASSWORD`, which psql reads, so it never shows in `ps` or shell history:

```bash
read -rs PGPASSWORD; export PGPASSWORD   # the owner's password
psql "$OWNER_URL" -c 'CREATE ROLE gaugeprep_dev_migrator LOGIN' -c 'CREATE ROLE gaugeprep_dev_app LOGIN'
psql "$OWNER_URL" -c '\password gaugeprep_dev_migrator'
psql "$OWNER_URL" -c '\password gaugeprep_dev_app'
(cd backend && uv run python -m config.db_roles gaugeprep_dev_migrator gaugeprep_dev_app) | psql "$OWNER_URL" -v ON_ERROR_STOP=1
unset PGPASSWORD
```

A role SQL run also takes over objects owned by another migration role (a branch copied from a split environment) when the owner can reach them, and stops with an error if any table or sequence is still not owned by the migration role. It revokes CONNECT from every role except the owner and the pair. On a rebuilt database, run it again after the first deploy has migrated: new tables get full data grants by default, and the rerun narrows `django_migrations`.

Then set `DATABASE_URL` (serving role) and `MIGRATION_DATABASE_URL` (migration role), same database, in the Doppler config (`doppler secrets set <KEY> --project gaugeprep --config dev`) and deploy. To rotate a password, run `\password <role>` as the owner, update that role's Doppler key and redeploy; rotate one role at a time.

Verify, with the serving role's URL without password in `$APP_URL` and `read -rs PGPASSWORD; export PGPASSWORD` set to that role's password:

```bash
psql "$APP_URL" -c 'CREATE TABLE t (i int)'                          # permission denied
psql "$APP_URL" -c 'ALTER TABLE django_migrations ADD COLUMN x int'  # must be owner
psql "$APP_URL" -c 'SELECT count(*) FROM procrastinate_jobs'         # works
curl -s https://dev.gaugeprep.com/api/v1/health                      # {"status":"ok","database":"ok"}
unset PGPASSWORD
```

Rollback: set `DATABASE_URL` in Doppler back to the migration role's URL and redeploy; the app runs as owner again, as before the split. The role SQL can be re-run at any time: tables made append-only keep select and insert only, and a trigger on them refuses update, delete and truncate even for a role that holds the privilege.

### Warning

The deploy user is in the docker group, which is root on the server: its key can read both environments' settings. Both hold synthetic data only; production gets its own server and key. One kamal-proxy serves both environments. Rebooting the server, or `kamal proxy reboot` or `kamal setup` from either destination, interrupts dev and staging together.

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

## CI workflows

### Trigger

A workflow in `.github/workflows/` changes. Workflow files are owner-only: a pull request stages the new file and the owner copies it in before merge.

### Steps

Workflow steps keep their shell inline and their comments short and tagged; the reasoning below is what the comments used to carry. Job names stay as they are (`gate`, `check`, `semgrep`, `pip-audit`, `pnpm-audit`, `trivy`, and `checks / ...` in the Pages run), since they are the checks the merge reads.

Security reasoning that used to sit in workflow comments:

- Scanners are free binaries or pinned packages, no token or account. The gitleaks and Trivy binaries are used instead of their actions (the gitleaks action needs a paid licence on organisations). Semgrep rules are the community repo pinned to a commit (Semgrep Rules License v1.0 allows internal CI use), metrics off.
- The `gate` job runs the path filter, secret scan, API check and scanner settings first; the PR title script comes from the pull request, so it runs last and cannot change their results. A failed secret scan, API check or title check skips the jobs that need `gate`; a failed scanner settings step alone does not, so the code and scanner jobs still run and the pull request stays red. A skipped job counts as passing for merge, so only the red `gate` blocks.
- Secret scan: the history reachable from the head, not other branches. The config and ignore list come from the base commit, the checkout's `.gitleaksignore` is removed and allow comments are off, so a pull request cannot switch off its own scan.
- API check: both specs come from git objects, so nothing in the checkout touches it. oasdiff is built from source because the release binary ships a Go standard library CVE; its output hash is pinned and checked after every cache restore, so a poisoned cache entry cannot run. It runs with an empty config and our own severity file, and external references refused.
- Scanner settings: pull requests only, because on a push it would block every publish after the owner merges over it. Docs and the owner-only workflow are not searched, since they describe the markers. The local Semgrep rules come from the base, so every change under `tooling/semgrep/` is flagged, deletions included. The step prints file names, field names and line numbers, never values.
- Semgrep and Trivy: ignore files and config come from the base commit (Semgrep drops every `.semgrepignore` and restores the base's; Trivy's inline markers are rewritten). On a push with neither a base nor a first parent, no ignore files are used. The first pull request that adds local rules is scanned without them; the `Local rule tests` step covers it. The test snippets hold unsafe calls on purpose, so that one file is excluded from the scan.
- pnpm audit: runs on a rebuilt directory (the lockfile with top-level fields allowlisted, plus fresh manifests and a workspace file), so no pull request setting, hook or `.npmrc` is read.
- Pull request title check: the template is read from the base commit, and the title and body reach the script only through environment variables, never inside the run text.
- `ci` has no secrets; the test PostgreSQL credentials are test-only. Called from the Pages run, it gets none of the Pages tokens, and each Pages job reads only its own prefix's secrets.
- The alarm workflows: GitHub refuses a direct push that edits or deletes `develop-alarm.yml` because the agent token lacks the workflow scope. Only an issue the workflow opened with the exact title counts as the alarm, and a renamed one does not, since titles and bodies are editable by anyone.
- Runners: arm64 GitHub-hosted runners are free for public repositories only, so this private repository uses x64.

### Verify

Open a pull request with a planted failure (a secret-shaped string, a changed scanner ignore file, a breaking `/api/v1` change) and read that the same job goes red as before the change: `gate` for the secret scan, API check and scanner settings, `semgrep`, `pip-audit`, `pnpm-audit` or `trivy` for their scans. Close the pull request without merging.

### Rollback

Copy the previous workflow file back in (the owner commits it).
