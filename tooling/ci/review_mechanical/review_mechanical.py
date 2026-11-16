"""Mechanical review checks on the lines a branch adds, run before the first push.

Usage: python review_mechanical.py --base origin/develop [--text-file pr-body.md]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

CODE_SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".ts", ".tsx", ".js", ".mjs", ".toml"}
SELF_DIR = "tooling/ci/review_mechanical/"
EM_DASH = "—"
COMMENT = re.compile(r"^\s*(#|//)(?!!)")
BANNER = re.compile(r"^\s*(#|//)\s*([-=*#~_]{3,}|[0-9]+\.\s|#region|MARK:)")
TODO = re.compile(r"\bTODO\b(?!\(#\d+\))")
SUPPRESSION = re.compile(
    r"(# noqa|# type: ignore|eslint-disable-next-line|nosemgrep)"
    r"(\[[^\]]*\]|:\s*[A-Z0-9, ]+)?(?P<reason>.*)$"
)
SIGNATURE = re.compile(r"Co-Authored-By|Generated with", re.I)
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def added_lines(diff: str) -> list[tuple[str, int, str]]:
    """(path, line number, text) for each line a `git diff -U0` adds."""
    out: list[tuple[str, int, str]] = []
    path, number = "", 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].removeprefix("b/") if line != "+++ /dev/null" else ""
        elif m := HUNK.match(line):
            number = int(m[1])
        elif line.startswith("+") and not line.startswith("+++") and path:
            out.append((path, number, line[1:]))
            number += 1
    return out


def agent_names(root: Path) -> set[str]:
    return {p.stem for p in (root / ".claude" / "agents").glob("*/*.md")}


def check_code(path: str, number: int, text: str) -> list[str]:
    if Path(path).suffix not in CODE_SUFFIXES or not COMMENT.match(text):
        return []
    found = []
    if len(text) > 100:
        found.append(
            f"issue: {path}:{number} - comment over 100 characters - shorten it"
        )
    if BANNER.match(text):
        found.append(f"issue: {path}:{number} - banner or section marker - delete it")
    if TODO.search(text):
        found.append(f"issue: {path}:{number} - TODO without a ticket - use TODO(#n)")
    return found


def check_suppression(path: str, number: int, text: str) -> list[str]:
    if Path(path).suffix not in CODE_SUFFIXES:
        return []
    m = SUPPRESSION.search(text)
    if m and len(m["reason"].strip(" -#:")) < 3:
        return [f"issue: {path}:{number} - suppression without a reason - add it"]
    return []


def check_prose(label: str, number: int, text: str, names: set[str]) -> list[str]:
    found = []
    if EM_DASH in text:
        found.append(f"issue: {label}:{number} - em dash - use a comma, colon or ' - '")
    if SIGNATURE.search(text):
        found.append(f"issue (blocking): {label}:{number} - tool signature - delete it")
    return found


def check_pr_text(text: str, names: set[str]) -> list[str]:
    pattern = re.compile(
        r"\.claude\b|/lm-[a-z]+|/pm\b|\b("
        + "|".join(sorted(map(re.escape, names)))
        + r")\b"
    )
    return [
        f"issue: PR text:{i} - names a tool or role file - say what changed instead"
        for i, line in enumerate(text.splitlines(), 1)
        if pattern.search(line)
    ]


def run(base: str, text_file: str | None) -> list[str]:
    root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
    )
    diff = subprocess.check_output(
        ["git", "diff", "-U0", f"{base}...HEAD"], text=True, cwd=root
    )
    log = subprocess.check_output(
        ["git", "log", "--format=%B", f"{base}..HEAD"], text=True, cwd=root
    )
    names = agent_names(root)
    findings: list[str] = []
    for path, number, text in added_lines(diff):
        if path.startswith(SELF_DIR):
            continue
        findings += check_code(path, number, text)
        findings += check_suppression(path, number, text)
        findings += check_prose(path, number, text, names)
    for i, line in enumerate(log.splitlines(), 1):
        findings += check_prose("commit messages", i, line, names)
    if text_file:
        body = Path(text_file).read_text()
        findings += check_pr_text(body, names)
        for i, line in enumerate(body.splitlines(), 1):
            findings += check_prose("PR text", i, line, names)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/develop")
    parser.add_argument("--text-file")
    args = parser.parse_args()
    findings = run(args.base, args.text_file)
    print("\n".join(findings) if findings else "mechanical checks: clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
