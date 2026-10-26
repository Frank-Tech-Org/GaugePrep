---
name: lm-brief
description: The LinguaMentor daily brief. Covers the milestone and sprint state, what shipped, the ticket in flight, blockers, decisions waiting on the owner, and the one ticket to work on today. Reads GitHub only; cheap.
disable-model-invocation: true
---

# Daily brief

## Data

!`.claude/scripts/board.sh list || true`
!`gh pr list --state merged --base develop --search "merged:>=$(date -d '1 day ago' +%F)" --json number,title || true`
!`gh api repos/LinguaMentor/linguamentor-v3/milestones --jq '.[] | "\(.title) · \(.closed_issues) closed / \(.open_issues) open · due \(.due_on // "-")"' || true`
!`sed -n '/^## Open/,/^## Decided/p' docs/DECISIONS.md || true`

## Do

Delegate to `delivery-manager` with the data above. It reads no source files. For the ticket in the slot only, it reads the last checkpoint with `gh issue view <n> --comments`.

Format, under 25 lines, with no preamble:
```
## LinguaMentor: <date>
**Sprint** <name> · <done>/<planned> · <on track | at risk | slipping>, and why in one line
**Milestone** <title> · <closed>/<total>
**Shipped since yesterday**: one line per merged PR, with the issue number
**In flight**: #<n> · <column> · <agent> · <last checkpoint's Next>
**Blocked**: #<n> waits on #<m>
**Needs your decision**: numbered from docs/DECISIONS.md, each with its recommendation and cost of delay
**Risk**: the one thing that bites in two weeks
```

End with exactly one line: `Run: /lm-<command> <n>` and the reason in under 15 words.
