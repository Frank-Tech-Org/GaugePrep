# Code comments

Applies to code files: source, tests, settings, scripts, Dockerfiles, Compose, Kamal and CI YAML, and the example env file. Docs (`*.md`) are not covered.

Good names come first; most blocks need no comment. A comment says only what the code can't: a non-obvious reason, a constraint, a trap.

## Limits

- At most 100 characters per line and two lines per comment. Longer reasoning goes in the PR, an ADR or a runbook, with a pointer (`# See ADR-011.`) if the reader needs it.
- Place a comment at the top of a file or above a complete block (function, class, settings group, workflow step), never line by line.

## Allowed

| Kind | Where | Form |
|---|---|---|
| File header | workflows, scripts, Dockerfiles, deploy and compose files, settings modules | one sentence: what the file is for |
| Usage header | shell scripts | `# Usage: bootstrap.sh <host>` |
| Block comment | above a block with a non-obvious reason | a tag: `WHY:`, `SECURITY:` (an invariant a refactor must keep) or `WARNING:` (a trap) |
| `TODO(#n):` | anywhere | always with a ticket number |
| Docstring | each module's `public.py` and everything `examcore` exports | Google style; one summary line, `Args`/`Returns`/`Raises` only when the type hints don't say it |
| Doctest | optional, `examcore` pure functions only | `>>> count_words("Bonjour !")` then the result; anything needing setup is a test |
| TSDoc | exported web hooks, utilities and shared components | one summary line, `@param` only when the type doesn't say it |
| Suppression | `# noqa`, `# type: ignore[...]`, `eslint-disable-next-line`, `nosemgrep` | always with the reason on the same line |
| Inline | units and magic values | `timeout = 2  # seconds` |
| Group heading | config files only: the example env, settings, compose, deploy configs | a blank line, then `# Database`: one short noun, nothing after it |

## Never

- Banners, boxes, rulers, short markers, underlines, numbered sections, editor regions or fold markers (`/*****/`, `# ----- X -----`, `# --- X ---`, `# ===`, `# 1. X`, `// #region`, `// MARK:`, `# {{{`). A code file that needs sections is doing two jobs.
- Narrative paragraphs, history (`changed on…`, `we used to…`), who decided, ticket narration.
- Restating the code, a name or a type. "This function…", "ensures that…".
- Commented-out code.
- Explanations in the example env file. Where a value comes from goes in the deploy runbook.

## The example env file

One group per environment or service, each with a one-word heading, a blank line between groups. Keys of the same kind sit together, and `DEV_` and `STAGING_` keys come in the same order so they pair up.

```dotenv
# Dev
DEV_SERVER_HOST=
DEV_DATABASE_URL=
DEV_DJANGO_SECRET_KEY=

# Staging
STAGING_SERVER_HOST=
STAGING_DATABASE_URL=
STAGING_DJANGO_SECRET_KEY=
```

## Example

```yaml
# Bad: narrative, one long line per thought
# Scans the full history reachable from the head, not other branches. Config and ignore list come from the base commit, so a PR cannot switch off its own scan.

# Good: tagged, short, the script holds the detail
# SECURITY: gitleaks config and ignore list come from the base commit.
- name: Scan the full git history
  run: .github/scripts/scan-history.sh
```

Workflow steps with more than about 10 lines of script move to `tooling/ci/`, where they get a usage header, shellcheck and tests.
