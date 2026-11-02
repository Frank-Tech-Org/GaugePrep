# Code comments

Applies to code files: source, tests, settings, scripts, Dockerfiles, Compose and CI YAML. Docs (`*.md`) are not covered.

- Comment only what the code can't say: a non-obvious reason, a constraint, a trap. Never restate the code, a name or a type.
- Place a comment at a file's entry or above a complete block (a function, class, settings group, service), never scattered line by line.
- One line, two at most. Few per file; most blocks need none.
- Docstrings only when they add something the name and signature don't.
- Write like a developer leaving a note for a teammate: plain and terse. No "This function...", no "ensures that...", no padded or generated-sounding phrasing.
- Why a dependency or design was chosen goes in the PR or an ADR, not the file.

```python
# Bad: restates the code, one note per line
def parse_database_url(url: str) -> dict[str, Any]:
    parts = urlsplit(url)  # split the URL
    name = parts.path.lstrip("/")  # get the database name

# Good: one note above the block, saying what the code can't
# Errors never echo the URL: it holds the password.
def parse_database_url(url: str) -> dict[str, Any]:
    parts = urlsplit(url)
    name = parts.path.lstrip("/")
```
