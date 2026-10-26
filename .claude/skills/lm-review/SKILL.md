---
name: lm-review
description: Review the open PR for a LinguaMentor ticket. Move it to In review, run the tech lead and the specialist reviewers on the real diff, post the verdict on the PR, and route fixes back to the builder.
argument-hint: <issue-number>
disable-model-invocation: true
---

# Review #$ARGUMENTS

## 1. Find the PR

```
gh pr list --state open --search "Refs #$ARGUMENTS in:body" --json number,title,headRefName,baseRefName
```
There must be exactly one, from `feature/$ARGUMENTS-*` into `develop`, or from `hotfix/*` into `main`. Otherwise say what's wrong and stop.

```
.claude/scripts/board.sh move $ARGUMENTS "In review"
gh pr diff <pr>
gh pr checks <pr>
```
If `gh pr diff` or `gh pr checks` fails (the classic-projects GraphQL error), use the REST calls: `gh api repos/LinguaMentor/linguamentor-v3/pulls/<pr>/files --paginate` for the diff and `gh api repos/LinguaMentor/linguamentor-v3/commits/<sha>/check-runs` for the checks.
```
gh issue view $ARGUMENTS
```

## 2. Review

Run these on the diff. Paste the ticket's acceptance criteria into each prompt.
- Always `tech-lead`.
- The reviewers for the ticket's Area, from the table in `CLAUDE.md`.
- The code reviewers in `.claude/agents/review/` for what the diff touches: `python-reviewer` for `.py`, `django-reviewer` for backend modules and endpoints, `database-reviewer` for migrations and SQL, `typescript-reviewer` for `.ts`/`.tsx`, `react-reviewer` for `.tsx` components, and `silent-failure-hunter` for grading, scoring, payment or error-handling code.
- `security-engineer` if the diff touches authentication, sessions, billing or payments, `identity`, migrations, append-only tables, AI prompts, the internal API or infrastructure exposure.
- `privacy-counsel` if it changes what personal data is collected, kept, logged or sent to a provider or to analytics.
- `ux-designer` and `ui-designer` if it changes what a learner sees.
- `performance-engineer` if it touches a learner page's bundle, media, a hot query or the grading or voice path.
- `product-verifier` if it changes learner-facing claims or copy.

Each reviewer also checks the Definition of Done items in the ticket that fall in its area.

## 3. Post

One short PR comment, `gh pr comment <pr> --body-file <file>`, at most 10 lines plus findings, verdict first, no recap or praise:
- The verdict per reviewer, one line each.
- Each blocker or fix as `file:line — problem — fix`.
- Unmet acceptance criteria and unticked Definition of Done items, by name.
- The final line, alone on its line, with the PR's head commit: `REVIEW: PASS <full head sha>` or `REVIEW: CHANGES <full head sha>`. Get the sha with `gh api repos/LinguaMentor/linguamentor-v3/pulls/<pr> --jq .head.sha`. A new commit makes an earlier verdict stale, so review again.

## 4. Next

- CHANGES: send the findings to the building agent. It fixes them on the same branch, commits (`fix(<area>): address review on #$ARGUMENTS`), and pushes. Then run this review again. After three rounds without a pass, stop and ask me.
- PASS on a hotfix into `main`, or on any PR that changes the guard hook, settings, CI workflows or the push and merge scripts: tell the owner it is ready to merge. `tech-lead` does not merge these.
- PASS with CI green on any other PR into `develop`: `tech-lead` merges, by running `.claude/scripts/merge.sh <pr>` on its own. The script squash-merges into `develop` only if the base, branch, checks and the PASS verdict (newer than the last commit) all hold, then deletes the branch. Then run `/lm-qa $ARGUMENTS`. If the script refuses, fix what it names; don't merge another way.

Post the checkpoint comment from `CLAUDE.md` (stage: In review) on the issue.
