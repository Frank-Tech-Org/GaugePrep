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
gh issue view $ARGUMENTS
```

## 2. Review

Run these on the diff. Paste the ticket's acceptance criteria into each prompt.
- Always `tech-lead`.
- The reviewers for the ticket's Area, from the table in `CLAUDE.md`.
- `security-engineer` if the diff touches authentication, sessions, billing or payments, `identity`, migrations, append-only tables, AI prompts, the internal API or infrastructure exposure.
- `privacy-counsel` if it changes what personal data is collected, kept, logged or sent to a provider or to analytics.
- `ux-designer` and `ui-designer` if it changes what a learner sees.
- `performance-engineer` if it touches a learner page's bundle, media, a hot query or the grading or voice path.
- `product-verifier` if it changes learner-facing claims or copy.

Each reviewer also checks the Definition of Done items in the ticket that fall in its area.

## 3. Post

One PR comment, `gh pr comment <pr> --body-file <file>`, made of:
- The verdict per reviewer, one line each.
- The blockers and fixes as `file:line`, the issue and the fix.
- Unmet acceptance criteria.
- The final line: `REVIEW: PASS` or `REVIEW: CHANGES`.

## 4. Next

- CHANGES: send the findings to the building agent. It fixes them on the same branch, commits (`fix(<area>): address review on #$ARGUMENTS`, with the co-author trailer), and pushes. Then run this review again. After three rounds without a pass, stop and ask me.
- PASS with CI green: tell me the PR is ready for me to squash-merge and delete the branch. After I merge, run `/lm-qa $ARGUMENTS`.

Post the checkpoint comment from `CLAUDE.md` (stage: In review) on the issue.
