# Owner-apply files

Agents cannot edit the hook, `settings.json` or the workflows (that is the point), so these wait here for you to copy. Run in your own terminal, from the repo root, after the reset PR is merged:

```bash
cp .claude/proposed/guard-bash.sh .claude/hooks/guard-bash.sh
cp .claude/proposed/settings.json .claude/settings.json
mkdir -p .github/workflows
cp .claude/proposed/main-alarm.yml .github/workflows/main-alarm.yml
chmod +x .claude/hooks/guard-bash.sh
sudo apt install -y jq
```

Then commit them on a branch of your own and merge. Check with `git diff` first; the old `PUSH_SHA` pin in the hook goes away because the new guard does not pin a script hash.

| File | What it does |
|---|---|
| `guard-bash.sh` | Reads each command as real words, so a commit message that says "push" or a script with `$` passes, while a raw push, tag, `--amend`, `reset --hard`, `gh pr merge`, release, `rm -rf /` and secret-file reads are blocked |
| `settings.json` | Same allow list as today, plus deny rules for `git push`, `gh pr merge` and `gh release`, so the block holds even if the hook is skipped |
| `main-alarm.yml` | Opens an issue when a commit lands on `main` outside a release or hotfix PR |

## Bot account (10 minutes, free)

1. Create a second GitHub account, for example `linguamentor-agents`, with its own email.
2. Invite it to the organisation as a member and give it **Write** on this repo only.
3. Create a fine-grained token for it limited to this repo (Contents, Pull requests, Issues: read and write; Projects: read and write) and put it in the machine's `gh auth login`.
4. Your own account stays the only one that merges into `main`, tags and publishes releases.
