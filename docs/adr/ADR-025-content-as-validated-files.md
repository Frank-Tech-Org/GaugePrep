# ADR-025: Content authored as validated files, imported into the content module

- Status: Proposed
- Date: 2026-11-05

## Context

Release 1 needs about 1,200 items, 250 prompts and tasks, 200 lessons and 3,000 vocabulary entries (PRD Section 11). Most drafting and first-line review is done by agents that work through GitHub pull requests. The architecture (Section 6.9) describes authoring in the internal console. Agents work best with files, diffs and CI checks; the console remains the right place for human approval, publication and the audit log (PRD CMS-2, CMS-8).

The content kit in `docs/content/` defines 8 JSON Schemas (common, listening item, reading item, writing prompt, speaking task, simulation form, lesson, vocabulary entry). They use `$ref` across files, `if`/`then`, `allOf` and `patternProperties`, so a hand-written checker would run past 200 lines and drift from the JSON Schema standard. Files need a real JSON Schema 2020-12 validator.

## Decision

- Content is authored as JSON files under `content/`, one file per version, validated in CI against the schemas in `docs/content/schemas` and by the copying check of `docs/content/originality-and-sources.md`.
- The schemas are checked with `jsonschema-rs`, which is already in the lockfile (see the dependency check below). The content validator that wraps it has its own ticket.
- An approved batch is imported into the `content` module by `manage.py content_import` as versions with status "approved". Publication happens in the console. The database is the source of truth for what learners see.
- Editing a published version is not possible in either place: a new version file is added and imported.
- The console keeps CMS-1 editing for human reviewers' small corrections; a correction made in the console is exported back to a new version file by `manage.py content_export` so the repository never falls behind.

## Dependency check: jsonschema-rs

Decided under D-11 (standing delegation): a free MIT dependency with no open CVE and no new lockfile packages. Checked on 2026-11-05.

| Check | Result |
|---|---|
| Package | `jsonschema-rs` 0.60.3 on PyPI, Python bindings of the Rust `jsonschema` crate |
| Already in the lockfile | Yes, 0.60.3, pulled in by Schemathesis (the API test tool) |
| New lockfile packages | None. Its only declared extras are `bench` and `tests`; no runtime dependencies |
| Licence | MIT (PyPI metadata) |
| Last release | 0.60.3, 27 October 2026; releases every week or two in October 2026 |
| Open CVEs | None. OSV returns no advisories for `jsonschema-rs` (PyPI) or `jsonschema` (crates.io) |
| Standard support | JSON Schema drafts 4 to 2020-12, including cross-file `$ref` |

## Alternatives considered

- **Console only.** Agents would need browser automation or a write API for every field, with no diffs or CI checks. Rejected.
- **Files only, no database versions.** Breaks append-only results that reference content versions in the database ([ADR-011](ADR-011-versioned-content-append-only-results.md)). Rejected.
- **Pure-Python `jsonschema`.** Also MIT and standard-complete, but it would add packages to the lockfile for no gain over a library we already ship. Rejected.
- **Hand-written checks.** Over 200 lines for the constructs above, and they would drift from the schemas. Rejected.

## Consequences

- The `content` module needs the import and export commands in M1.
- CI gains a content job (validator and copying check) that runs only when `content/` changes.
- Audio is generated after import and never stored in Git.
- Today `jsonschema-rs` is only in the lockfile because Schemathesis needs it. The validator declares it as a direct dev dependency when it lands, so a Schemathesis upgrade can't drop it silently.
