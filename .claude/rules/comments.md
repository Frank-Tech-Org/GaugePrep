# Code comments

Applies to every file an agent writes: code, tests, settings, YAML, Dockerfiles, scripts.

- Comment only what the code can't say: a non-obvious reason, a constraint, a trap. Never restate the code, a name or a type.
- One line, two at most. Few per file; most functions need none.
- Docstrings only when they add something the name and signature don't. No module docstring unless the file's purpose isn't obvious from its path.
- Write like a developer leaving a note for a teammate: plain and terse. No "This function...", no "ensures that...", no padded or generated-sounding phrasing.
- Why a dependency or design was chosen goes in the PR or an ADR, not the file.

```python
# Bad: restates the code
# Set the connect timeout to the timeout value
options["connect_timeout"] = connect_timeout

# Good: says what the code can't
# Short, so a down database answers 503 instead of hanging the request.
options["connect_timeout"] = connect_timeout
```
