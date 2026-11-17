# Automation account token

Purpose: replace the automation account's broad classic token with a fine-grained one limited to this repository.

## Trigger

The account `KefouegFrank` still uses the classic token (scopes `gist`, `project`, `read:org`, `repo`), or the fine-grained token is within a week of its 90-day expiry. Branch rules and alarms are in the branching process doc, section 9.

## Prerequisites

- [ ] Organisation owner access to `Frank-Tech-Org`.
- [ ] A shell on the automation machine. `frankkefoueg` is never logged in to `gh` there.

## Steps

1. Organisation Settings, Personal access tokens: allow fine-grained tokens (approval required is fine). Expect: the setting saved.
2. As `KefouegFrank`, create a fine-grained token: owner `Frank-Tech-Org`, only `GaugePrep`, 90 days; read and write Contents, Pull requests, Issues; read Metadata, Actions, Commit statuses; no Workflows; organisation Projects read and write. Expect: the token shown once.
3. Approve the request as organisation owner if GitHub asks. Expect: status active.
4. Remove the old login: `gh auth logout -u KefouegFrank`. Expect: logged out.
5. Log in: `gh auth login --with-token` and paste the token. Expect: no error.
6. Wire git: `gh auth setup-git`. Expect: no output.

## Verify

1. `gh auth status`. Pass: `KefouegFrank` only, with a fine-grained token.
2. `gh pr list --limit 1`. Pass: lists PRs.
3. Push a branch that edits a workflow file. Pass: GitHub refuses it (no Workflows permission).

## Rollback

1. `gh auth logout -u KefouegFrank`.
2. `gh auth login --with-token` with the previous token if it is still valid, else a new classic token with the old scopes.
3. Run Verify 1.

## What the guard refuses

The guard on the automation machine is a speed bump; the develop alarm is the net. It reads through `bash -c`, `sh -c`, `eval`, `env`, `sudo`, `timeout`, `xargs`, `find -exec`, `$(...)`, newline-separated commands, a full path to `git`, git aliases and `git -c` settings. It refuses:

- git options and environment variables that name a program to run (including abbreviations such as `--exe=`), and exported editor, pager and `GIT_*` variables
- text piped into a shell, function and `trap` bodies, `git-*` programs, `git subtree`, and `uv run`, `pnpm exec` or `doppler run` wrapping git
- GitHub calls that read a query from a file, switch workflows off, change repository settings or send a GraphQL mutation, and `curl` or `wget` writes to GitHub (including `-sXPUT`)
- `git credential`, `gh auth` printing a token, writes under `~/.config/gh`, keyring access, `cd` it cannot follow, and writes over a folder holding owner-only files

Accepted gaps: scripts or tests the automation writes and then runs; a `core.hooksPath` in the owner's global git config; split-string tricks such as `$(echo git) push`; wrappers such as `strace`, `unbuffer`, `parallel`, `make -f -`; `gh repo sync --force` from a fork and `gh run cancel` on an alarm run (the alarm and its hourly recheck cover both); `gh variable delete` and `gh secret delete`; uppercase API paths (GitHub returns 404); reading the `gh` hosts file.
