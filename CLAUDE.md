# GaugePrep

Exam preparation platform for TCF Canada first: a responsive, mobile-first web app installable as a PWA (Next.js), a Django modular monolith, a LiveKit voice examiner and a shared `examcore` rules package. Sources of truth:

- Product: `docs/product/PRD.md`
- Architecture: `docs/architecture/system-architecture.md`, decisions in `docs/adr/`
- Exam rules: `docs/exam-specs/TCF-Canada.md`
- How work flows: `docs/process/branching-and-release.md`

## Rules that always apply

- **Parallel tickets, never overlapping.** At most 2 tickets are in flight (In progress, In review, In QA), 3 once CI runs on every PR. Each has its own branch. The one being built uses the owner's checkout, so the owner sees the work; any other in flight uses its own git worktree (switching rules in the `lm-next` skill). Two run together only if their Areas or paths differ and neither blocks the other. `/pm` picks the set; `/lm-next` refuses an overlap. Owner-run tickets with no repository code (accounts, recordings, vendor requests) run outside the limit, one at a time; one only waiting on a third party doesn't count. See the process doc §1 for blocking and hotfixes.
- **Brief.** Reviews, comments, reports and checkpoints are short: verdict first, at most 10 lines, findings as `file:line — problem — fix`, no recap, no praise.
- **Branches and environments.** `develop` (default) deploys to dev, `stage` to staging, `main` to production on a tag. Code moves forward only, by merge-commit PRs the owner merges; a hotfix starts on `main` and is merged back into `stage`, then `develop`. See the process doc §3.
- **Agents commit and open PRs; `/lm-next` merges into `develop`; the owner releases.** Inside a `/lm-*` command, agents create the ticket's branch from the ticket (`gh issue develop`), so the branch and PR show in its Development panel, then commit to it, push it and open the PR. A ticket that writes nothing into the repository gets no branch and no PR; its result goes on the ticket. After the review step of `/lm-next` posts `REVIEW: PASS`, CI is green and the owner has approved that commit on GitHub (a sign-off, not a second review), the merge step of `/lm-next` is the only merge, by running `.claude/scripts/merge.sh <pr>`, which squash-merges into `develop` and refuses anything else. Only the owner merges into `stage` and `main`, pushes tags and publishes releases. Agents push only with `.claude/scripts/push.sh <work-branch> [--force-with-lease]`, which pushes to the branch of the same name. The guard hook and the deny rules in `.claude/settings.json` block raw `git push`, `gh pr merge`, merges and ref, tag or release writes through `gh api`, tags, releases, `--amend`, `reset --hard`, writes to owner-only files and reads of secret files.
- **One branch and one PR per setup effort.** Changes to the team, commands, hooks or process go on one `chore/*` branch and one PR until that effort is finished; later fixes are new commits on it, never a new PR.
- **Commits** follow Conventional Commits, `<type>(<area>): <subject>`, with one commit per logical step. Never add a `Co-Authored-By` trailer, a "Generated with Claude Code" line or any similar tool signature to a commit message, PR body, issue, comment or file; the owner doesn't want any of it anywhere.
- **GitHub admin is fine.** Moving board items, editing labels and fields, and posting issue or PR comments through `gh` are allowed. Before a bulk write (more than five issues), state the scope and confirm it.
- **Only `product-manager` writes tickets.** Any other agent that finds work (a failed QA check, a budget breach, a false claim, a missing blocker) writes a draft with a title, type, suggested area and priority, context, and steps or evidence, then hands it to `product-manager`. `product-manager` creates it in Ideas, or adds it to an existing ticket if it's a duplicate. Creating or editing more than five at once needs the owner's go-ahead.
- **Every ticket has acceptance criteria and a Definition of Done.** Criteria say what the user sees; the DoD says how we know it is finished well (tests, accessibility, budgets, migrations, security, docs), each item measurable.
- **Ticket titles have no type prefix, and tickets that have not started have no comments.** The Type field says chore or decision; Conventional Commit prefixes are for commits and PR titles. Checkpoint comments start when work starts.
- **Tickets stand alone.** An issue body never points at the PRD, the architecture doc, ADR numbers or exam-spec sections. Inline the facts the reader needs. Ticket and PR text (bodies, comments, checkpoints) never names a slash command; it says which role does the next step and what it is, like "qa-engineer checks each criterion on dev".
- **PR text is short.** One or two sentences of summary, `Refs #<n>`, what changed, and only the checklist items that matter. Titles follow Conventional Commits.
- **Write like the developer who did the work.** Tickets name no files or paths. PRs and comments name a path only when the reviewer needs it, and never name `.claude` files, agents or slash commands; commands the owner must run stay in. Plain, specific, human, nothing that reads generic or generated (`.claude/rules/writing.md`).
- **Write plainly.** Code comments are rare and brief: one or two lines at a file's entry or above a complete block, saying what the code can't, in a developer's voice (`.claude/rules/comments.md`). Longer reasoning goes in the PR or an ADR.
- **Progressive by milestone.** Tickets and code are written for the current milestone only; later work, including the build pack's parts, waits for its milestone. Changes not tied to a ticket go on the open setup PR's branch; every other branch and PR links to a ticket.
- **`.env.example` mirrors `.env`.** Both hold the same keys. A ticket that adds a setting adds the key to `.env.example`, runs `.claude/scripts/env-check.sh --add` (key names only, never values) and lists the keys under "Owner: paste values for" in the PR. Agents never read `.env`.
- **Free or self-hosted in dev and staging; paid only in production.** Before relying on a free plan, check its limits and terms cover the work. If they don't, adopt the best free or self-hosted alternative and report it in the PR, or draft a decision for `product-manager`.

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
| `/pm [plan \| decide \| report]` | planning | Bare: takes the `cto` agent's technical read, says what is done, what to start next and what needs the owner. `plan` sorts Ideas, writes acceptance criteria and the DoD, fills the sprint. `decide` resolves owner decisions. `report` posts the weekly delivery report to Notion |
| `/lm-next [block <blocker>]` | Ready → Ready to deploy | Moves the ticket nearest done one step: build, fix, review, merge or QA, resuming from its checkpoint; starts the next ticket when there is room; records a blocker |
| `/lm-release [version] \| check` | Ready to deploy → Done | Due when a key feature is complete, at sprint end for fixes, and once M0 is complete; `/pm` says when. `check`: the release gate alone (security, performance budgets, public claims). Otherwise, with the version worked out from the last tag: changelog, promotion PR `develop` → `stage`, gate and regression on staging, release PR `stage` → `main`, notes, then post "Released in" on the tickets and move them to Done after the owner tags |
| `/lm-hotfix` | interrupt | Production fix from `main` |

**Commands take no ticket number.** Each reads the board, the current branch or worktree, open PRs and the last checkpoint, works out its target, checks the environment allows it (parallel limit, overlap, blockers, CI, a verdict for the current head), and either proceeds or names the command to run instead. `#n` is an optional override only. Every command ends by naming the next command. `/lm-release` works out the next version from the last tag; a version given overrides it.

Board helper used by the commands: `.claude/scripts/board.sh` (list, wip, info, move, block, unblock, set, type, sprint).

## Team

18 agents live in `.claude/agents/<department>/`. No session is special: whichever session or scheduled job runs a command runs the team through it, and gets technical judgment from the `cto` agent.

| Department | Agents |
|---|---|
| Direction | `cto`, `product-manager`, `business-analyst` |
| Engineering | `backend-engineer`, `frontend-engineer`, `scoring-engineer`, `platform-engineer`, `ai-engineer`, `voice-engineer` |
| Quality | `qa-engineer`, `performance-engineer`, `security-engineer`, `code-reviewer` |
| Design | `brand-designer`, `product-designer` |
| Content and growth | `exam-content-lead`, `content-marketer` |
| Compliance | `privacy-compliance` |

**`cto`** owns the architecture, ADRs, `docs/process/` and `.claude/`, writes the technical read `/pm` passes to `product-manager`, decides technical Decision tickets and checks every new dependency; see `.claude/agents/direction/cto.md`.

`code-reviewer` is read-only and reviews every diff once, covering the architecture invariants, Python, Django, SQL, TypeScript, React, silent failures and changes to `.claude/`. Security review and attack testing are `security-engineer`; attacks run only against staging or a local copy, never production or third parties.

**Skills and rules.** Each agent preloads only the skills its role needs (the `skills:` list in its file) and is told not to load others. Stack rules for Python and the web are in `.claude/rules/`, and the `/lm-*` commands are skills named `lm-*` in `.claude/skills/`.

**Routing by the issue's Area field** (used by `/lm-next`):

| Area | Builds | Reviews |
|---|---|---|
| web | `frontend-engineer` (after `product-designer` if there is no spec) | `code-reviewer`, `qa-engineer` |
| api | `backend-engineer` | `code-reviewer`, `qa-engineer` |
| examcore | `scoring-engineer` | `code-reviewer`, `qa-engineer` |
| grading | `ai-engineer` | `scoring-engineer`, `security-engineer` |
| voice | `voice-engineer` | `code-reviewer`, `qa-engineer` |
| content | `exam-content-lead` for exam items; `content-marketer` for public pages, help centre, blog and campaigns; `brand-designer` for brand and visuals | `product-manager` |
| payments | `backend-engineer` | `security-engineer`, `code-reviewer` |
| infra | `platform-engineer` (also releases and runbooks) | `security-engineer` |
| compliance | `privacy-compliance` | `product-manager` |
| docs | the agent that owns the documented area; `cto` for process docs and ADRs | `code-reviewer` |

Decision tickets go to `cto` (technical) or `product-manager` (product) and produce an ADR. Anything touching authentication, payments, personal data, migrations or append-only tables also gets `security-engineer` review.

## Quality gates

- **Security, all free tools.** CI runs Semgrep, Gitleaks, `pip-audit`, `pnpm audit` and Trivy on every PR; HIGH or CRITICAL blocks the merge. `security-engineer` runs ZAP and Nuclei on staging weekly, and before each release leads a pentest itself in a Claude Code session (no paid API): ZAP active scan, Nuclei, Schemathesis against the OpenAPI contract, sqlmap and ffuf on suspect endpoints, and the permanent attack tests. Targets are only systems we own: staging or a local copy, never production or third parties. A finding closes only when the same attack fails.
- **Performance.** `performance-engineer` holds the PRD budgets with Lighthouse on slow 3G in CI and a weekly k6 run on staging. A breach is a Bug ticket, and a fix ships with a guard.
- **Weekly demo, Friday.** The owner tries the app on staging, on a phone and a computer, and reads two scorecards: security findings and performance budgets. The day before, `/pm report` has `product-manager` post the delivery report in the Notion database "Weekly demos": the 13 key features of release 1 delivered against those still to deliver, launch readiness, performance and security, in product terms with no ticket numbers.
- **Design approval.** `brand-designer` and `product-designer` show the owner two or three options (a Figma file or a comparison page); only the approved one enters the repo. Logos and tokens live in the repo as SVG and token files.
- **Sources.** Imported agents, skills and rules are listed with source and licence in `.claude/SOURCES.md`.

## Definition of Done

The lists live in the issue templates' "Definition of Done" field (`.github/ISSUE_TEMPLATE/task.yml`, `story.yml`, `chore.yml`, `bug.yml`). `/pm plan` keeps the items that apply, deletes the rest and writes the list into the ticket body beside the acceptance criteria, so every ticket carries its own. The review and QA steps of `/lm-next` tick them, and an unticked item is a fail.

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

Every command that changes a ticket ends by posting this on the issue. It is how `/lm-next` picks up with no other context, so write it for a reader who knows nothing. One line per field.

```text
**Checkpoint** · <stage> · <agent> · <YYYY-MM-DD>
Branch: <branch or "none">
Done: <what is finished, in plain words>
Verified: <commands that passed, or "nothing yet">
Next: <the role and the exact next step, never a slash command>
Needs the owner: <decision or action, or "nothing">
```

## Lessons and memory

- Agents keep no memory files. A lesson worth keeping (a recurring defect, a ruling, a provider quirk) becomes a one-line edit to the agent's own file or to `.claude/rules/`, in the same PR as the work, so it is reviewed and nothing piles up.
- The project memory is `.claude/memory/`, read by `cto` and by the session running the commands: one index, `MEMORY.md`, and a file per standing fact, updated in place, never duplicated. Memory changes go in the commit with the work they came from. It is selected by `autoMemoryDirectory` in `.claude/settings.local.json`, which needs an absolute path, so each machine sets its own:
  `{ "autoMemoryDirectory": "/absolute/path/to/checkout/.claude/memory" }`
