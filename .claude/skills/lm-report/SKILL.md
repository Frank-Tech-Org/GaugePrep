---
name: lm-report
description: The LinguaMentor weekly report. Covers velocity and trend, the milestone forecast against its date, what shipped, defect clusters, decisions waiting, and the plan for next week. Reads GitHub and agent memory only.
disable-model-invocation: true
---

# Weekly report

## Data

!`gh issue list --state closed --search "closed:>=$(date -d '7 days ago' +%F)" --json number,title,labels --limit 100 || true`
!`gh pr list --state merged --search "merged:>=$(date -d '7 days ago' +%F)" --json number,title,baseRefName --limit 100 || true`
!`gh api repos/LinguaMentor/linguamentor-v3/milestones --jq '.[] | "\(.title) · \(.closed_issues) closed / \(.open_issues) open · due \(.due_on // "-")"' || true`
!`.claude/scripts/board.sh list || true`

## Do

Delegate to `delivery-manager`, with `product-owner` for the recommendation. Give it the data above, the open entries in `docs/DECISIONS.md`, and the `MEMORY.md` files of `qa-engineer`, `security-engineer` and `performance-engineer` under `.claude/agent-memory/`. It doesn't read source.

Format, under 60 lines:
```
# LinguaMentor: week of <date>

## Milestone
<title> · <closed>/<total> · <on track | at risk | slipping>, and why in one sentence.

## Velocity
Tickets reaching Ready to deploy this week: <n> (last week: <n>) · trend
At this rate the milestone finishes around <date>.

## Shipped
One line per ticket: #n, and what a learner or operator can now do.

## Defect clusters
Up to three recurring problem areas, with the count and the structural fix.

## Decisions waiting on you
Numbered: the question · the recommendation · the cost of delay.

## Next week
The three tickets that move the milestone furthest, in order, with the reason.
```
Skip any section with nothing in it. Don't pad.
