# Writing tickets, PRs and comments

Applies to everything we post on GitHub: issue bodies, PR titles and bodies, review and QA comments, checkpoints. Code comments follow `comments.md`.

Write as the developer who did the work, to a colleague who will act on it. Plain, specific, a little informal. If it could have been written about any project, rewrite it.

## Tickets

- No file names, paths or directories. Say what the user sees or what part of the product changes, in words ("the CI check", "the health endpoint", "the board helper").
- No agent names, slash commands or internal tooling names. Name the role only when a handover matters ("QA checks it on dev").
- Say why it matters in one or two sentences, then what done looks like.

## Pull requests

- A summary a teammate can read in ten seconds: what changed and why, in the first person where it helps ("I moved...", "I found that...").
- Name a path only when the reviewer needs it to find the change, and then only the one or two that matter. Never list every touched file; the diff does that.
- Never name `.claude` files, agents, skills or slash commands. If the change is to the team's own setup, say what behaves differently now.
- Commands the owner has to run stay in, exact and short. Don't narrate steps already done.
- Risks and follow-ups in plain sentences, only when there are any.

## Comments and checkpoints

- Verdict first, then findings as `label: file:line — problem — fix`. The path is fine there; it is the point.
- Labels: `issue (blocking)`, `issue`, `suggestion`, `nit`, `question`. Only a blocking issue holds the merge.
- Don't recap the diff, thank anyone or list what you checked. Say what you found.
- Avoid stock phrases: "ensures", "robust", "comprehensive", "seamless", "leverage", "it is worth noting", "in order to", and the "not X, but Y" reveal. Prefer a plain verb.
- Numbers and results as they came out. If something failed or was skipped, say so first.

```text
Bad:  "Updates `.claude/scripts/board.sh`, the three `lm-*` skills and `docs/process/branching-and-release.md` to ensure the renamed organisation is used consistently."
Good: "The board helper and release steps still pointed at the old org, so they 404'd after the rename. They use the new names now."
```
