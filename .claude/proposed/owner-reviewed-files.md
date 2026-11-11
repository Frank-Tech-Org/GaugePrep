# Let agents edit workflows and scanner config on branches

Today agents can't touch the CI workflows, the scanner ignore and config files or the npm and pnpm config, so every change to them comes to you as a file to copy. This keeps the merge with you but lets agents write those files on a work branch:

- **Still blocked everywhere:** the hooks, both settings files, `push.sh` and `merge.sh`. An agent that could edit these could switch off its own guard.
- **Writable on a branch, merged only by you:** `.github/workflows/`, `.semgrepignore`, `.trivyignore*`, `trivy.yaml`, `.gitleaks.toml`, `.gitleaksignore`, `.npmrc`, `.pnpmfile.*`. The merge script refuses any PR that touches them, and CI already flags a scanner-setting change.

Risk: a workflow on a pushed branch runs with the repository secrets before you review it. Today those are only the dev and staging Pages tokens. Keep production secrets in a GitHub Environment limited to `main` before production deploys exist.

## 1. `.claude/hooks/guard-bash.sh`, lines 80 to 82

Replace:

```python
# Owner-only files: hooks, settings, the push and merge scripts, CI workflows, scanner ignore files and config, npm/pnpm config.
OWNER_ONLY = re.compile(r"\.claude/(hooks/|settings(\.local)?\.json|scripts/(push|merge)\.sh)|\.github/workflows/"
                        r"|(\.semgrepignore|\.trivyignore[\w.-]*|(?<![\w.-])trivy\.yaml|\.gitleaks\.toml|\.gitleaksignore|\.npmrc|\.pnpmfile\.[\w.-]*)(?![\w.-])")
```

with:

```python
# Owner-only files: the guard itself. Workflows and scanner config are writable; merge.sh sends those PRs to the owner.
OWNER_ONLY = re.compile(r"\.claude/(hooks/|settings(\.local)?\.json|scripts/(push|merge)\.sh)")
```

## 2. `.claude/settings.json`, `permissions.deny`

Delete the 24 `Edit`, `Write` and `MultiEdit` lines for `.semgrepignore`, `.trivyignore*`, `trivy.yaml`, `.gitleaks.toml`, `.gitleaksignore`, `.npmrc` and `.pnpmfile.*`. Keep everything else.

## 3. `.claude/scripts/merge.sh`, line 40

Replace the pattern inside `test(...)`:

```text
^\\.claude/(hooks/|settings|scripts/(push|merge)\\.sh)|^\\.github/workflows/|^\\.gitleaks(\\.toml|ignore)$
```

with:

```text
^\\.claude/(hooks/|settings|scripts/(push|merge)\\.sh)|^\\.github/workflows/|(^|/)(\\.semgrepignore|\\.trivyignore[^/]*|trivy\\.yaml|\\.gitleaks\\.toml|\\.gitleaksignore|\\.npmrc|\\.pnpmfile\\.[^/]*)$
```

## Check

```bash
echo '{"tool_input":{"command":"echo x > .github/workflows/t.yml"}}' | .claude/hooks/guard-bash.sh; echo "exit $?"   # exit 0
echo '{"tool_input":{"command":"echo x > .claude/hooks/t.sh"}}' | .claude/hooks/guard-bash.sh; echo "exit $?"      # Blocked, exit 2
```

Then delete this file in the same commit.
