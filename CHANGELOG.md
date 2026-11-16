# Changelog

## v0.1.0 - 2026-11-16

First release. It proves the pipeline end to end: checks on every pull request, deploys to dev and staging, and the groundwork the first features build on. No learner-facing feature yet.

### Added

- Django backend skeleton on PostgreSQL 18 with a health endpoint and an OpenAPI document (#7)
- Module packages with Import Linter contracts that keep modules behind their public interfaces (#8)
- Word counting the way TCF Canada counts, in the shared exam-rules package (#166)
- One command, `pnpm check`, for formatting, linting and types (#4)
- Git hooks for commit messages, formatting and secret scanning (#5)
- Pull request checks: lint, types, tests, security scanners with a full-history secret scan, Semgrep rules for unsafe eval and exec, and a build of the backend image (#6, #68, #102, #108)
- Gate on pull requests for titles and descriptions, API breaking changes, missing migrations, changed scanner settings and shell script lint (#88, #89, #87, #93, #151)
- Test rules: branch coverage floors, no skips, random order, success, not-found and refused tests for every endpoint, Schemathesis against the OpenAPI document, 90% coverage on changed backend lines (#84, #85, #86, #148)
- Release check workflow skeleton for the grader (#20)
- Script that rebuilds the dev and staging server from a blank machine (#10)
- Dev and staging deploys to the shared server with Kamal, with secrets from Doppler, a separate migration database role and a staging database, DNS record and secrets (#11, #179, #181, #182)
- Placeholder pages for dev and staging on Cloudflare Pages (#150)
- Backend image build and deploy to dev on `develop` and to staging on `stage` (#106)
- Content kit, exam specs and anchor rules for the first milestone (#53)

### Changed

- The product is GaugePrep across the repository, and the local database is named `gaugeprep` (#147, #198)
- Apps sit side by side under one layout, and our CI checks live in one tooling folder (#186)
- Scanner ignore files and config are owner-only, and the scanner-settings flag no longer stops the code and scanner jobs (#94, #149)
- Pull request title, secret-scan and change checks run as one gate job (#109)
- Pages are published only after the pull request checks pass (#167)
- Helper scripts can no longer push straight to `develop` (#189)
- Workflows and config comments follow the comment rules, and decision records have readable file names (#187, #188)
- Decisions recorded: production deploys on the owner's tag with no approval gate, test strategy and CI minutes budget, speech recognition chosen by a public-corpus benchmark, Notch Pay sandbox and signature confirmed (#12, #83, #15, #17)

### Fixed

- A blank host list falls back to local hosts and the static files root is set (#80)
- The endpoint marker check counts async tests and uses strict markers (#110)
