# LinguaMentor

Exam preparation platform for TCF Canada first: a Next.js PWA, a Django modular monolith, a LiveKit voice examiner and a shared `examcore` rules package. Sources of truth:

- Product: `docs/product/PRD.md`
- Architecture: `docs/architecture/system-architecture.md`, decisions in `docs/adr/`
- Exam rules: `docs/exam-specs/TCF-Canada.md`
- How work flows: `docs/process/branching-and-release.md`

## Rules that always apply

- **Parallel tickets, never overlapping.** At most 2 tickets are in flight (In progress, In review, In QA), 3 once CI runs on every PR. Each has its own branch and git worktree, and two run together only if their Areas or paths differ and neither blocks the other. `/pm` picks the set; `/lm-start` refuses an overlap. See the process doc §1 for blocking and hotfixes.
- **Brief.** Reviews, comments, reports and checkpoints are short: verdict first, at most 10 lines, findings as `file:line — problem — fix`, no recap, no praise.
- **Agents commit and open PRs; `tech-lead` merges into `develop`; the owner releases.** Inside a `/lm-*` command, agents commit to the ticket's own branch, push it and open the PR. After `/lm-review` posts `REVIEW: PASS` and CI is green, only `tech-lead` merges, by running `.claude/scripts/merge.sh <pr>` on its own, which squash-merges into `develop` and refuses anything else. Only the owner merges into `main`, pushes tags and publishes releases. The guard hook blocks `gh pr merge`, `gh release create`, tags, `--amend`, force pushes and direct pushes to `main` or `develop`. Agents never run `git push`. They push with `.claude/scripts/push.sh <work-branch> [--force-with-lease]`, run as its own command, which checks the branch and pushes it to the branch of the same name. Any other command containing the word "push", commit messages included, is refused. Git commands must be written out literally: no `$`, backticks, `$(...)` or heredocs, so commit messages go in plain `-m "..."` strings.
- **Commits** follow Conventional Commits, `<type>(<area>): <subject>`, with one commit per logical step. Never add a `Co-Authored-By` trailer, a "Generated with Claude Code" line or any similar tool signature to a commit message, PR body, issue, comment or file; the owner doesn't want any of it anywhere.
- **GitHub admin is fine.** Moving board items, editing labels and fields, and posting issue or PR comments through `gh` are allowed. Before a bulk write (more than five issues), state the scope and confirm it.
- **Only `pm` writes tickets.** Any other agent that finds work (a failed QA check, a budget breach, a false claim, a missing blocker) writes a draft with a title, type, suggested area and priority, context, and steps or evidence, then hands it to `pm`. `pm` creates it in Ideas, or adds it to an existing ticket if it's a duplicate. Creating or editing more than five at once needs the owner's go-ahead.
- **Every ticket has acceptance criteria and a Definition of Done.** Criteria say what the user sees; the DoD says how we know it is finished well (tests, accessibility, budgets, migrations, security, docs), each item measurable.
- **Tickets stand alone.** An issue body never points at the PRD, the architecture doc, ADR numbers or exam-spec sections. Inline the facts the reader needs.
- **PR text is short.** One or two sentences of summary, `Refs #<n>`, what changed, and only the checklist items that matter. Titles follow Conventional Commits.
- **Write plainly.** Code comments: one or two lines saying why. Longer reasoning goes in the PR or an ADR.

## Architecture invariants (review blockers)

- `examcore` never imports Django. Every exam rule lives there once.
- Modules talk only through their `public.py`; each module owns one PostgreSQL schema; Import Linter enforces it.
- Grades, paper scores and predictions are append-only and store every version that produced them.
- Personal data lives only in `identity`; other tables use the anonymous learner ID. No name, email or phone in AI requests.
- Learner text and transcripts go to models as delimited data, never as instructions; outputs are schema-validated.
- Async work goes through the transactional outbox (Procrastinate on PostgreSQL), in the same transaction as the change.
- Migrations are expand-then-contract.

## Commands

| Command | Stage | What it does |
|---|---|---|
| `/pm [triage \| refine <n\|all> \| plan \| block <n> <b> \| decide \| resume [n] \| report]` | any | The project manager. Bare: asks `tech-lead`, says what is done and what to start next, in order. The arguments triage Ideas, write ACs and DoD, plan the sprint, record blockers, resolve owner decisions, resume from checkpoints |
| `/lm-start <n>` | → In progress | Check limit and overlap, own worktree and branch, route to the owning agents, build and test |
| `/lm-review <n>` | → In review | Review the PR diff and post the verdict |
| `/lm-qa <n>` | → In QA | Verify on staging; pass to Ready to deploy or fail back |
| `/lm-release <version>` | Ready to deploy → Done | Full release gate, release branch and PR, notes, then close tickets after the owner tags |
| `/lm-verify-claims [surface]` | before release | Check every public claim against code and tests; refresh `docs/CLAIMS.md` |
| `/lm-perf-audit [target]` | before release | Measure against the performance budgets; open a ticket per breach |
| `/lm-hotfix <n>` | interrupt | Production fix from `main` |

Board helper used by the commands: `.claude/scripts/board.sh` (list, wip, info, move, block, unblock, set, type, sprint).

## Team

Agents live in `.claude/agents/<department>/`. Each keeps its memory in `.claude/agent-memory/<agent>/`.

| Department | Agents |
|---|---|
| Direction | `pm`, `tech-lead` |
| Engineering | `backend-django`, `frontend-nextjs`, `examcore-scoring`, `ai-grading-engineer`, `voice-engineer`, `qa-engineer` |
| Design | `ux-designer`, `ui-designer` |
| Engineering (quality) | `performance-engineer`, `product-verifier` |
| Platform | `devops-sre`, `security-engineer`, `release-manager` |
| Content | `exam-content-author`, `technical-writer` |
| Compliance | `privacy-counsel` |
| Growth | `product-analyst`, `copywriter-seo` |
| Review (code) | `python-reviewer`, `django-reviewer`, `database-reviewer`, `typescript-reviewer`, `react-reviewer`, `silent-failure-hunter` |

The review agents are read-only specialists. `tech-lead` calls them in `/lm-review` by what the diff touches: Python, Django, migrations or SQL, TypeScript, React, and any code that handles errors, grades, scores or payments (`silent-failure-hunter`). Security review is `security-engineer`.

**Skills and rules.** Each agent preloads only the skills its role needs (the `skills:` list in its file) and is told not to load others. Stack rules for Python and the web are in `.claude/rules/`, and the `/lm-*` commands are skills named `lm-*` in `.claude/skills/`.

**Routing by the issue's Area field** (used by `/lm-start`):

| Area | Builds | Reviews |
|---|---|---|
| web | `frontend-nextjs` (after `ux-designer` if there is no spec) | `tech-lead`, `qa-engineer` |
| api | `backend-django` | `tech-lead`, `qa-engineer` |
| examcore | `examcore-scoring` | `tech-lead`, `qa-engineer` |
| grading | `ai-grading-engineer` | `examcore-scoring`, `security-engineer` |
| voice | `voice-engineer` | `tech-lead`, `qa-engineer` |
| content | `exam-content-author` | `pm` |
| payments | `backend-django` | `security-engineer`, `tech-lead` |
| infra | `devops-sre` | `security-engineer` |
| compliance | `privacy-counsel` | `pm` |
| docs | `technical-writer` | the owner of the documented area |

Decision tickets go to `tech-lead` (technical) or `pm` (product) and produce an ADR. Anything touching authentication, payments, personal data, migrations or append-only tables also gets `security-engineer` review.

## Definition of Done

The lists live in the issue templates' "Definition of Done" field (`.github/ISSUE_TEMPLATE/task.yml`, `story.yml`, `chore.yml`, `bug.yml`). `/pm refine` keeps the items that apply, deletes the rest and writes the list into the ticket body beside the acceptance criteria, so every ticket carries its own. `/lm-review` and `/lm-qa` tick them, and an unticked item is a fail.

The items are measurable on purpose:
- each endpoint has success, not-found and other-learner-refused tests
- axe-core reports zero serious or critical violations
- the stated performance budgets hold

Don't soften them into "handled" or "considered".

## Decisions

Anything that needs the owner goes in `docs/DECISIONS.md` as a numbered entry with options, a recommendation and the cost of delay. `/pm` surfaces it and `/pm decide` resolves it. These always need the owner:
- scoring or grading formula changes
- a new paid service or dependency
- destructive migrations
- auth redesign
- pricing
- cutting milestone scope
- anything that costs money or can't be undone

## Checkpoint comment

Every command that changes a ticket ends by posting this on the issue. It is how `/pm resume` picks up with no other context, so write it for a reader who knows nothing. One line per field.

```text
**Checkpoint** · <stage> · <agent> · <YYYY-MM-DD>
Branch: <branch or "none">
Done: <what is finished, with file paths>
Verified: <commands that passed, or "nothing yet">
Next: <the exact next step>
Needs the owner: <decision or action, or "nothing">
```

## Memory

- Agent memory: `.claude/agent-memory/<agent>/`, committed with the repo.
- General Claude Code memory: `.claude/memory/`. It is selected by `autoMemoryDirectory` in `.claude/settings.local.json`, which needs an absolute path, so each machine sets its own:
  `{ "autoMemoryDirectory": "/absolute/path/to/linguamentor-v3/.claude/memory" }`
