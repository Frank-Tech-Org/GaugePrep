# Let agents edit scanner and npm config on branches

Agents can't touch the scanner ignore and config files or the npm and pnpm config today, so every change to them comes to you as a file to copy. This lets agents write those on a work branch; the merge script sends any PR that touches them to you, and CI already turns red on a scanner-setting change. Gitleaks and Semgrep read their config from the base branch, so a branch can't quietly weaken its own scan.

Workflows stay locked. A workflow on a pushed branch runs before review and can grant its own token write access; with no branch protection, that token could push to `develop` or `main`. This also closes a gap that exists today: the Edit and Write tools aren't denied on workflows, so only the token's missing Workflows permission stops one reaching GitHub.

## 1. `.claude/hooks/guard-bash.sh`, lines 80 to 82

Replace:

```python
# Owner-only files: hooks, settings, the push and merge scripts, CI workflows, scanner ignore files and config, npm/pnpm config.
OWNER_ONLY = re.compile(r"\.claude/(hooks/|settings(\.local)?\.json|scripts/(push|merge)\.sh)|\.github/workflows/"
                        r"|(\.semgrepignore|\.trivyignore[\w.-]*|(?<![\w.-])trivy\.yaml|\.gitleaks\.toml|\.gitleaksignore|\.npmrc|\.pnpmfile\.[\w.-]*)(?![\w.-])")
```

with:

```python
# Owner-only: the guard and CI workflows. Scanner and npm config are owner-merged by merge.sh.
OWNER_ONLY = re.compile(r"\.claude/(hooks/|settings(\.local)?\.json|scripts/(push|merge)\.sh)|\.github/workflows/")
```

## 2. `.claude/settings.json`, `permissions.deny`

Delete lines 76 to 96: the 21 `Edit`, `Write` and `MultiEdit` rules for `.semgrepignore`, `.trivyignore*`, `trivy.yaml`, `.gitleaks.toml`, `.gitleaksignore`, `.npmrc` and `.pnpmfile.*`. In their place add:

```json
      "Edit(./.github/workflows/**)",
      "Write(./.github/workflows/**)",
      "MultiEdit(./.github/workflows/**)",
```

## 3. `.claude/scripts/merge.sh`, lines 39 and 40

Replace the comment on line 39 with:

```bash
# Guard files, workflows, CI scripts, scanner and npm config are merged by the owner.
```

and the pattern inside `test(...)` on line 40:

```text
^\\.claude/(hooks/|settings|scripts/(push|merge)\\.sh)|^\\.github/workflows/|^\\.gitleaks(\\.toml|ignore)$
```

with:

```text
^\\.claude/(hooks/|settings|scripts/(push|merge)\\.sh)|^\\.github/(workflows|scripts)/|^semgrep/|(^|/)(\\.semgrepignore|\\.trivyignore[^/]*|trivy\\.ya?ml|\\.gitleaks\\.toml|\\.gitleaksignore|\\.npmrc|\\.pnpmfile\\.[^/]*|pnpm-workspace\\.yaml)$
```

## Check

```bash
echo '{"tool_input":{"command":"echo x > .trivyignore"}}' | .claude/hooks/guard-bash.sh; echo "exit $?"          # exit 0
echo '{"tool_input":{"command":"echo x > .github/workflows/t.yml"}}' | .claude/hooks/guard-bash.sh; echo "exit $?"  # Blocked, exit 2
```

Then delete this file in the same commit.
