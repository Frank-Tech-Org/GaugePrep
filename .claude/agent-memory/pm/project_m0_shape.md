---
name: m0-shape
description: M0 dependency chain, ticket sizing concerns and the non-code tickets, as refined on 2026-10-26
metadata:
  type: project
---

M0 chain set on 2026-10-26: #4 blocks #5, #6 and #7. #7 blocks #8. #9 blocks #10, #17 and #18. #6, #7 and #10 block #11. #11 and #12 block #13. #14 blocks #15. #6 blocks #20.

Sizing flagged as over two days (the owner decides on splits): #14 (20 speakers, weeks of elapsed time), #15 (3 providers x 60 recordings), and #11 is borderline. Compare these against actuals when they close.

Non-code, owner-run tickets: #9, #14, #16, #17, #18 and #19. Whether they count against the in-flight limit is open as D-2 in docs/DECISIONS.md.

Ownership of shared files: #5 owns `.gitleaks.toml` and the commitlint config, and #6 only reads them, so #5 and #6 can run in parallel once #4 lands.

#9 is split into an agent part (untrack the committed `.env`, `.env.example`, ad hoc gitleaks) and an owner part (accounts, secrets). Secret naming waits on D-3: the private repo on GitHub Free has no environments, so the default is repo secrets prefixed STAGING_/PROD_ unless the owner pays for Team. As of 2026-10-28 D-3 was still not written in docs/DECISIONS.md, and #12 (prod approval gate) hinges on the same paid-plan question.

Recurring stall: a PASS PR waits days for tech-lead to run merge.sh (#45, PASS 2026-10-26, unmerged 2026-10-28). No staging exists in M0, so /lm-qa for infra chores cannot run "on staging".

**Why:** this records the reasoning behind the order, so a later session doesn't re-derive it or undo it.

**How to apply:** check the board before relying on this; update the sizing notes with actuals.
