# Automation account and push guard

The automation commits, pushes and merges into `develop` as `KefouegFrank`. Its limits are its token, a deny list and a guard on the machine that runs it. Branch rules and the alarms are in the branching process doc, section 9.

## Replace the token with a fine-grained one

Today the account uses a classic token with the scopes `gist`, `project`, `read:org` and `repo`, broader than needed: any shell past the guard could use it for repository-admin calls. Replace it:

1. In the organisation's Settings, Personal access tokens: allow fine-grained tokens (approval required is fine).
2. Signed in as `KefouegFrank`, create a fine-grained token: resource owner `Frank-Tech-Org`, only `GaugePrep`, 90 days. Read and write: Contents, Pull requests, Issues. Read: Metadata, Actions, Commit statuses (fine-grained tokens can't have Checks, so tools read CI from Actions runs). Leave Workflows out, so the account can't push workflow changes. Organisation permission Projects: read and write.
3. Approve the token request as organisation owner if GitHub asks.
4. On the automation machine: `gh auth logout -u KefouegFrank` for any broader login, then `gh auth login --with-token` (paste the token), `gh auth setup-git` and `gh auth status`.

The owner account `frankkefoueg` is never logged in to `gh` on that machine: the owner approves, merges into `stage` or `main`, tags and releases in the browser or as another OS user.

## What the guard refuses

The guard is a speed bump; the develop alarm is the net. It reads through `bash -c`, `sh -c`, `eval`, `env`, `sudo`, `timeout`, `xargs`, `find -exec`, `$(...)`, newline-separated commands, a full path to `git`, git aliases and `git -c` settings that can run commands. It refuses:

- git options and environment variables that name a program to run, including abbreviated ones such as `--exe=`, and exported editor, pager and `GIT_*` variables
- text piped or fed into a shell, function and `trap` bodies, `git-*` programs, `git subtree`, and `uv run`, `pnpm exec` or `doppler run` wrapping git
- GitHub calls that read a query from a file, switch workflows off, change repository settings or send a GraphQL mutation, and `curl` or `wget` writes to GitHub, including combined flags such as `-sXPUT`
- `git credential`, `gh auth` printing a token, writes under `~/.config/gh`, any `secret-tool` or keyring access, `cd` it cannot follow, and writes over a whole folder that holds owner-only files

A script the automation runs without a prompt must not be one it can edit, or a push could be hidden inside it.

## Accepted gaps

The guard is a tripwire against ordinary and accidental pushes, not a sandbox; the alarm is the backstop.

- a script, test file or package script the automation writes and then runs goes unprompted, as does a `core.hooksPath` in the owner's global git config
- split-string tricks such as `$(echo git) push`, python-built command strings and a helper path assembled from pieces
- wrappers such as `strace`, `unbuffer`, `parallel` and `make -f -`
- `gh repo sync --force` from a fork; the alarm still flags the commit
- `gh run cancel` on an alarm run; the hourly recheck covers it
- `gh variable delete` and `gh secret delete`
- uppercase API paths; GitHub answers them with a 404, so they do nothing
- reading the `gh` hosts file
