# Writing tickets, PRs, comments and docs

Applies to everything we post on GitHub (issue bodies, PR titles and bodies, review and QA comments, checkpoints), to commit messages and to the docs we commit (ADRs, runbooks, process docs, READMEs). Code comments follow `comments.md`.

Write as the developer who did the work, to a colleague who will act on it. Plain, specific, a little informal. If it could have been written about any project, rewrite it.

## Everywhere

- First person and plain verbs, as the person who did it: "I moved the check", "I couldn't reproduce it on dev". Never write as an agent or an assistant ("As requested...", "I have successfully..."). Review and QA comments too.
- Never mention anything under `.claude/`, agents, skills or slash commands. Say what behaves differently, or name the role ("QA checks it on dev").
- Never dump a list of directories or files. Name at most one or two paths, only where the reader needs them to find the change, and say what changed in words.
- Before you post or commit prose, run it through the `humanizer` skill and post only the rewrite.
- No em dashes anywhere. Use a comma, colon, period, parentheses or a spaced hyphen (` - `).
- Marketing copy (public pages, campaigns) also gets the Self-Check in `.claude/skills/copywriting/references/ai-tells.md`.

## Tickets

- No file names, paths or directories. Say what the user sees or what part of the product changes, in words ("the CI check", "the health endpoint", "the board helper").
- No agent names, slash commands or internal tooling names. Name the role only when a handover matters ("QA checks it on dev").
- Say why it matters in one or two sentences, then what done looks like.

## Pull requests

- A summary a teammate can read in ten seconds: what changed and why, in the first person where it helps ("I moved...", "I found that...").
- The diff lists the touched files; the PR doesn't. If the change is to the team's own setup, say what behaves differently now.
- Commands the owner has to run go in the chat reply, never in the PR. The PR says only that the owner copies in a staged file or merges. Don't narrate steps already done.
- Evidence holds real proof only: a before and after, a measured number against its budget, a run link, a screenshot. Routine check results are one ticked line each under "How it was tested"; never paste command output.
- Risks and follow-ups in plain sentences, only when there are any.

## Comments and checkpoints

- Verdict first, then findings as `label: file:line - problem - fix`. The path is fine there; it is the point.
- Labels: `issue (blocking)`, `issue`, `suggestion`, `nit`, `question`. Only a blocking issue holds the merge.
- Don't recap the diff, thank anyone or list what you checked. Say what you found.
- Avoid stock phrases: "ensures", "robust", "comprehensive", "seamless", "leverage", "it is worth noting", "in order to", and the "not X, but Y" reveal. Prefer a plain verb.
- Numbers and results as they came out. If something failed or was skipped, say so first.

## Docs

- Only what the reader needs to act or decide. No filler, no intro that restates the title, no closing recap.
- Headings name what the reader looks up ("Restore the database", "Rollback"), not "Overview", "Background" or "Conclusion".
- Short sections, lists and tables over paragraphs; one topic per doc, extended in place rather than a second doc beside it.

```text
Bad:  "Updates `.claude/scripts/board.sh`, the three `lm-*` skills and `docs/process/branching-and-release.md` to ensure the renamed organisation is used consistently."
Good: "The board helper and release steps still pointed at the old org, so they 404'd after the rename. They use the new names now."
```
