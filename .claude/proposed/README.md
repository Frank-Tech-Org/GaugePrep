# Owner-apply files

Agents cannot edit the hook, `settings.json`, the push and merge scripts or the workflows (that is the point), so changes to them wait here for you to copy. Run in your own terminal, from the repo root:

```bash
cp .claude/proposed/guard-bash.sh .claude/hooks/guard-bash.sh
sed -i '2s/only the tech-lead runs it/only the CTO (the main Claude Code session) runs it/' .claude/scripts/merge.sh
git diff .claude/hooks .claude/scripts
```

Then tell Claude it is done; it commits them on the setup branch and this folder is removed.

| Change | What it does |
|---|---|
| `guard-bash.sh` | Also blocks merges, ref, tag and release writes through `gh api` (REST and GraphQL), any command that changes a hook, settings, `push.sh`, `merge.sh` or a workflow, and checks secret-file reads per command, so `git ls-files .env \| head` is no longer a false alarm |
| `merge.sh` line 2 | The comment names the CTO instead of the removed tech-lead role |

## Bot account (10 minutes, free)

1. Create a second GitHub account, for example `linguamentor-agents`, with its own email.
2. Invite it to the organisation as a member and give it **Write** on this repo only.
3. Create a fine-grained token for it limited to this repo (Contents, Pull requests, Issues: read and write; Projects: read and write) and put it in the machine's `gh auth login`.
4. Your own account stays the only one that merges into `main`, tags and publishes releases.
