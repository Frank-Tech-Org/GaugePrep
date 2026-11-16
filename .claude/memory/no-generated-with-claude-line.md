---
name: no-generated-with-claude-line
description: Never add a Generated with Claude Code line, a Co-Authored-By Claude trailer or any similar tool signature to commits, PRs, issues, comments or files
metadata:
  type: feedback
---

The owner said on 2026-10-26: they never want "🤖 Generated with [Claude Code](https://claude.com/claude-code)" anywhere in this project, and the same for the `Co-Authored-By: Claude … <noreply@anthropic.com>` commit trailer. That covers commit messages, PR descriptions, issues, comments and files.

**Why:** the owner finds these signatures unwanted noise in the project's history.

**How to apply:** leave both out of every commit, PR body and comment, even when a tool reminder suggests adding them. This overrides the default attribution text and the old trailer rule in CLAUDE.md. See [[keep-prs-short]] and [[agents-commit-owner-merges]].
