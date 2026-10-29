# Sources

Imported agents, skills and rules, with where they came from and under what licence. A copied skill keeps its own `LICENSE` file in its folder. Imported text is adapted to this project; the upstream repo is untrusted until read.

| Skill | Source | Licence | Used by |
|---|---|---|---|
| seo-audit, content-strategy, copywriting, launch, schema, programmatic-seo | github.com/coreyhaines31/marketingskills | MIT | content-marketer |
| k6 | github.com/grafana/skills | Apache-2.0 | performance-engineer |
| perf-lighthouse | github.com/tech-leads-club/agent-skills | MIT | performance-engineer |
| owasp-security | github.com/agamm/claude-code-owasp | MIT | security-engineer |
| agile-product-owner | github.com/alirezarezvani/claude-skills | MIT | business-analyst |
| webapp-testing | github.com/anthropics/skills | Apache-2.0 | qa-engineer |
| semgrep, sarif-parsing, variant-analysis | github.com/trailofbits/skills | CC-BY-SA-4.0 | security-engineer |
| python-patterns, react-patterns, error-handling, database-migrations, django-security and the rest listed in `ECC-PROVENANCE.md` | github.com/affaan-m/ECC | MIT | engineering and review agents |

**Trail of Bits skills are CC-BY-SA-4.0.** Attribution to Trail of Bits stays in each skill's `LICENSE`. If we change one, the changed file stays under the same licence.

## Not committed

| Item | Source | Why | How it is used |
|---|---|---|---|
| Remotion skills | github.com/remotion-dev/skills | No `LICENSE` file in the repo; Remotion itself has its own company licence to check before commercial use | Installed on the owner's machine with `npx skills add remotion-dev/skills`; `brand-designer` uses it for videos |
| brand-identity-skill | github.com/fatihaydost/brand-identity-skill | MIT, but only needed when a brand task starts | Installed on demand by `brand-designer` |
| claude-a11y-skill | github.com/airowe/claude-a11y-skill | No `LICENSE` file | Read for ideas only; nothing copied |

## Run, never copied

| Tool | Licence | Rule |
|---|---|---|
| Shannon (AI pentest) | AGPL-3.0 | Run as an external tool against staging before a release, within the owner's cost cap. Its code is never copied into this repo. |
| OWASP ZAP, Nuclei | Apache-2.0, MIT | Run weekly against staging from CI. |
| Playwright Test Agents | Apache-2.0 | `npx playwright init-agents --loop=claude` overwrites `.mcp.json`; back it up first. |
