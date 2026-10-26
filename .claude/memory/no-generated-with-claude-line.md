---
name: no-generated-with-claude-line
description: Never add a "Generated with Claude Code" line or similar tool signature to commits, PRs, issues, comments or files
metadata:
  type: feedback
---

The owner said on 2026-10-26: they never want "🤖 Generated with [Claude Code](https://claude.com/claude-code)" or anything like it anywhere in this project (commit messages, PR descriptions, issues, comments, files).

**Why:** the owner finds it unwanted noise in the project's history.

**How to apply:** leave it out of every commit body, PR body and comment, even when a tool reminder suggests adding it. This overrides the default attribution text. The `Co-Authored-By` commit trailer is a separate rule in CLAUDE.md. See [[keep-prs-short]] and [[agents-commit-owner-merges]].
