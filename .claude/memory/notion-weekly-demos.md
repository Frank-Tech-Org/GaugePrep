---
name: notion-weekly-demos
description: Where the weekly report goes in Notion, who posts it, and that it reports product features, never tickets or process
metadata:
  type: reference
---

The owner chose Notion for the weekly report and Friday demo (2026-10-29). The private studio page (https://app.notion.com/p/4083ae0faeec81e090a9f2d9a6df4147) holds the "Weekly demos" database (https://app.notion.com/p/3ae280efae1e4a9ebce8b2499dccd65a, data source collection://b059f097-50cf-4c20-92d6-ce8d8d55a766). Properties: Week, Demo date, Status, Features delivered, Features to deliver, Security, Performance, Try it.

The report counts the 13 key features of release 1 (PRD §8.1 to §8.13): delivered this week in learner terms, a status row per feature, next week, the six launch conditions, measured performance and security, and risks to the launch date. No ticket or PR numbers, merges, board columns or agents. Decisions stay in `docs/DECISIONS.md`; one waiting on the owner appears only as a launch risk.

**Why:** on 2026-10-29 the owner said they care about measurable achievement against the product's key features ("this week, the login feature has been implemented"), not the board or how the team organises itself, and sessions are not always open.
**How to apply:** `product-manager` posts it through `/pm report` the day before the Friday demo, following the format in `.claude/skills/pm/SKILL.md`. The demo time is not fixed yet. See [[studio-reset-owner-decisions]].
