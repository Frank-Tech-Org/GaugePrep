# LinguaMentor

Exam preparation platform for TCF Canada first: a Next.js PWA, a Django modular monolith, a LiveKit voice examiner and a shared `examcore` rules package. Sources of truth:

- Product: `docs/product/PRD.md`
- Architecture: `docs/architecture/system-architecture.md`, decisions in `docs/adr/`
- Exam rules: `docs/exam-specs/TCF-Canada.md`
- How work flows: `docs/process/branching-and-release.md`

## Rules that always apply

- **One ticket at a time.** The work slot covers In progress, In review and In QA, and holds at most one ticket. Never start a second ticket while one is in it; see the process doc §1 for blocking and hotfixes.
- **Agents commit and open PRs; the owner merges and releases.** Inside a `/lm-*` command, agents commit to the ticket's own branch, push it and open the PR. Only the owner merges, pushes tags and publishes releases. The guard hook blocks `gh pr merge`, `gh release create`, tags, `--amend`, force pushes and direct pushes to `main` or `develop`.
- **Commits** follow Conventional Commits, `<type>(<area>): <subject>`, with one commit per logical step. Each ends with the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- **GitHub admin is fine.** Moving board items, editing labels and fields, and posting issue or PR comments through `gh` are allowed. Before a bulk write (more than five issues), state the scope and confirm it.
- **Only `product-owner` creates issues.** Any other agent that finds work (a failed QA check, a budget breach, a false claim, a missing blocker) writes a draft with a title, type, suggested area and priority, context, and steps or evidence, then hands it to `product-owner`. `product-owner` creates it in Ideas, or adds it to an existing ticket if it's a duplicate. Creating more than five at once needs the owner's go-ahead.
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
| `/lm-brief` | daily | Where we are, what shipped, what's blocked, decisions waiting, what to do today |
| `/lm-report` | weekly | Velocity, milestone forecast, defect clusters, decisions, next week |
| `/lm-decide` | any | Walk the open decisions in `docs/DECISIONS.md`, record the owner's answers, unblock tickets |
| `/lm-board [column]` | any | Summarise the board or one column and say what matters next |
| `/lm-triage` | Ideas → Backlog | Classify untriaged tickets, flag duplicates, accept them into the backlog |
| `/lm-refine <n>` | Backlog → Ready | Write acceptance criteria and dependencies, then move to Ready |
| `/lm-plan-sprint [sprint]` | Ready | Fill the sprint in dependency order |
| `/lm-next` | Ready | Name the single ticket to work on next |
| `/lm-start <n>` | → In progress | Take the slot, branch, route to the owning agents, build and test |
| `/lm-block <n> <blocker>` | In progress → Ready | Record a blocker and hand the slot to it |
| `/lm-review <n>` | → In review | Review the PR diff and post the verdict |
| `/lm-qa <n>` | → In QA | Verify on staging; pass to Ready to deploy or fail back |
| `/lm-release <version>` | Ready to deploy → Done | Full release gate, release branch and PR, notes, then close tickets after the owner tags |
| `/lm-verify-claims [surface]` | before release | Check every public claim against code and tests; refresh `docs/CLAIMS.md` |
| `/lm-perf-audit [target]` | before release | Measure against the performance budgets; open a ticket per breach |
| `/lm-hotfix <n>` | interrupt | Production fix from `main` |
| `/lm-resume [n]` | any | Rebuild context after `/clear`, a crash or a new day |

Board helper used by the commands: `.claude/scripts/board.sh` (list, wip, info, move, block, unblock).

## Team

Agents live in `.claude/agents/<department>/`. Each keeps its memory in `.claude/agent-memory/<agent>/`.

| Department | Agents |
|---|---|
| Direction | `product-owner`, `tech-lead`, `delivery-manager` |
| Engineering | `backend-django`, `frontend-nextjs`, `examcore-scoring`, `ai-grading-engineer`, `voice-engineer`, `qa-engineer` |
| Design | `ux-designer`, `ui-designer` |
| Engineering (quality) | `performance-engineer`, `product-verifier` |
| Platform | `devops-sre`, `security-engineer`, `release-manager` |
| Content | `exam-content-author`, `technical-writer` |
| Compliance | `privacy-counsel` |
| Growth | `product-analyst`, `copywriter-seo` |

**Routing by the issue's Area field** (used by `/lm-start`):

| Area | Builds | Reviews |
|---|---|---|
| web | `frontend-nextjs` (after `ux-designer` if there is no spec) | `tech-lead`, `qa-engineer` |
| api | `backend-django` | `tech-lead`, `qa-engineer` |
| examcore | `examcore-scoring` | `tech-lead`, `qa-engineer` |
| grading | `ai-grading-engineer` | `examcore-scoring`, `security-engineer` |
| voice | `voice-engineer` | `tech-lead`, `qa-engineer` |
| content | `exam-content-author` | `product-owner` |
| payments | `backend-django` | `security-engineer`, `tech-lead` |
| infra | `devops-sre` | `security-engineer` |
| compliance | `privacy-counsel` | `product-owner` |
| docs | `technical-writer` | the owner of the documented area |

Decision tickets go to `tech-lead` (technical) or `product-owner` (product) and produce an ADR. Anything touching authentication, payments, personal data, migrations or append-only tables also gets `security-engineer` review.

## Definition of Done

The lists live in the issue templates' "Definition of Done" field (`.github/ISSUE_TEMPLATE/task.yml`, `story.yml`, `chore.yml`, `bug.yml`). `/lm-refine` keeps the items that apply and deletes the rest, so every ticket carries its own list. `/lm-review` and `/lm-qa` tick them, and an unticked item is a fail.

The items are measurable on purpose:
- each endpoint has success, not-found and other-learner-refused tests
- axe-core reports zero serious or critical violations
- the stated performance budgets hold

Don't soften them into "handled" or "considered".

## Decisions

Anything that needs the owner goes in `docs/DECISIONS.md` as a numbered entry with options, a recommendation and the cost of delay. `/lm-brief` surfaces it and `/lm-decide` resolves it. These always need the owner:
- scoring or grading formula changes
- a new paid service or dependency
- destructive migrations
- auth redesign
- pricing
- cutting milestone scope
- anything that costs money or can't be undone

## Checkpoint comment

Every command that changes a ticket ends by posting this on the issue. It is how `/lm-resume` picks up with no other context, so write it for a reader who knows nothing.

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
