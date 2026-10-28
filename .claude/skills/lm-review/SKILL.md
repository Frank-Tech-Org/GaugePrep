---
name: lm-review
description: Review the right open LinguaMentor PR. Works out which PR from the current branch and the board, checks it is reviewable, runs the tech lead and specialist reviewers on the real diff, posts the verdict, and hands off to the next command.
argument-hint: "[#n to override]"
disable-model-invocation: true
---

# Review: $ARGUMENTS

No number is needed; `#n` only overrides the choice below.

## State now

!`.claude/scripts/board.sh wip || true`
!`git branch --show-current`
!`gh api "repos/LinguaMentor/linguamentor-v3/pulls?state=open" --jq '.[] | "#\(.number) \(.head.ref) -> \(.base.ref) \(.head.sha)"' || true`

## 1. Find the PR

In this order:
1. `#n` in the arguments (ticket or PR number).
2. The open PR whose branch is the current branch.
3. The open PR whose last `REVIEW:` comment is missing or names an older head sha than the PR's current head. If several, take the oldest.

The PR must be from `feature/<n>-*` into `develop`, or `hotfix/*` into `main`. The ticket is the `Refs #<n>` in its body.

## 2. Check the environment, hand off if it says no

| Finding | Hand off to |
|---|---|
| No open PR | `/lm-start`; or `/lm-qa` if a merged PR is waiting |
| Head sha already has `REVIEW: PASS` | merge (rules in §4) |
| CI failing | `/lm-start` (continues on the branch and fixes it); no review of red code |
| Branch behind `develop` with conflicts | `/lm-start` (rebases) |

Then `board.sh move <n> "In review"`, and read the diff (`gh pr diff <pr>`, or `gh api repos/LinguaMentor/linguamentor-v3/pulls/<pr>/files --paginate` when it fails) and the checks (`gh api repos/LinguaMentor/linguamentor-v3/commits/<sha>/check-runs`). Read the ticket with `gh issue view <n>`.

## 3. Review

Run these on the diff. Paste the ticket's acceptance criteria into each prompt.
- Always `tech-lead`.
- The reviewers for the ticket's Area, from the table in `CLAUDE.md`.
- The code reviewers in `.claude/agents/review/` for what the diff touches: `python-reviewer` for `.py`, `django-reviewer` for backend modules and endpoints, `database-reviewer` for migrations and SQL, `typescript-reviewer` for `.ts`/`.tsx`, `react-reviewer` for `.tsx` components, and `silent-failure-hunter` for grading, scoring, payment or error-handling code.
- `security-engineer` if the diff touches authentication, sessions, billing or payments, `identity`, migrations, append-only tables, AI prompts, the internal API or infrastructure exposure.
- `privacy-counsel` if it changes what personal data is collected, kept, logged or sent to a provider or to analytics.
- `ux-designer` and `ui-designer` if it changes what a learner sees.
- `performance-engineer` if it touches a learner page's bundle, media, a hot query or the grading or voice path.
- `product-verifier` if it changes learner-facing claims or copy.

Each reviewer also checks the Definition of Done items in its area.

Post one short PR comment (`gh pr comment <pr> --body-file <file>`, or REST if it fails), at most 10 lines plus findings, verdict first, no recap or praise: a verdict per reviewer, each fix as `file:line — problem — fix`, unmet criteria and unticked DoD items by name. The last line, alone: `REVIEW: PASS <full head sha>` or `REVIEW: CHANGES <full head sha>` (sha from `gh api repos/LinguaMentor/linguamentor-v3/pulls/<pr> --jq .head.sha`). A new commit makes it stale.

## 4. Next

- CHANGES: send the findings to the building agent, which fixes on the same branch (`fix(<area>): address review on #<n>`) and pushes. Run `/lm-review` again. After three rounds, stop and ask the owner.
- PASS on a hotfix into `main`, or on a PR that changes the guard hook, settings, CI workflows or the push and merge scripts: tell the owner it is ready to merge.
- PASS on any other PR into `develop` with CI green: `tech-lead` runs `.claude/scripts/merge.sh <pr>` on its own, then `/lm-qa`. While no CI exists the script refuses and the owner merges. If it refuses for another reason, fix what it names; don't merge another way.

Post the checkpoint comment from `CLAUDE.md` (stage: In review) on the issue.
