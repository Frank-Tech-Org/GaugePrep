---
name: lm-block
description: Mark the LinguaMentor ticket in flight as blocked by another ticket, release the work slot, and hand it to the blocker.
argument-hint: <blocked-issue> <blocker-issue>
arguments: [blocked, blocker]
disable-model-invocation: true
---

# #$blocked is blocked by #$blocker

## 1. Check

```
.claude/scripts/board.sh info $blocked
.claude/scripts/board.sh info $blocker
```
If `#$blocker` is itself blocked by `#$blocked`, stop: that is a cycle, and the owner and `product-owner` must split one of them.

If `#$blocker` doesn't exist yet, draft it with `product-owner` (title, type, area, a short context), show me, and create it only after my go-ahead.

## 2. Record

```
.claude/scripts/board.sh block $blocked $blocker
.claude/scripts/board.sh move $blocked Ready
```
Post the checkpoint comment from `CLAUDE.md` on `#$blocked`: stage Blocked, with what is done, what is waiting on `#$blocker`, and where to resume.

## 3. Hand the slot over

Save the work on `#$blocked`'s branch so the tree is clean:
```
git add <this ticket's paths>
git commit -m "wip(<area>): <what is done so far>" -m "Refs #$blocked" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -u origin <the feature branch>
```
Then the next step depends on where `#$blocker` is:
- Ready: `/lm-start $blocker`
- Backlog or Ideas: `/lm-refine $blocker` first

When `#$blocker` reaches Ready to deploy, `/lm-next` brings `#$blocked` back first.
