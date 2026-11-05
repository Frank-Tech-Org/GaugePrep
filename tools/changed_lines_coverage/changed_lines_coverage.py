"""Fail when too few executable backend lines a change touches are covered.

Usage: python changed_lines_coverage.py --base origin/develop
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


# Mirrors the coverage omit list, so these files are never expected in the report.
UNMEASURED = re.compile(r"(^|/)(tests|migrations)/|(^|/)(conftest|manage)\.py$")


def parse_diff(diff: str) -> dict[str, set[int]]:
    """Added or changed lines per backend .py file, from `git diff -U0`."""
    changed: dict[str, set[int]] = {}
    path: str | None = None
    header = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            header, path = True, None
        elif header and line.startswith("+++ "):
            name = line[4:].removesuffix(
                "\t"
            )  # git appends a tab after names with spaces
            if name.startswith('"') and "backend/" in name:
                raise ValueError(f"cannot read the quoted path {name}")
            ok = name.startswith("b/backend/") and name.endswith(".py")
            path = name[2:] if ok and not UNMEASURED.search(name) else None
        elif line.startswith("@@"):
            header = False
            if path and (m := HUNK.match(line)):
                start, count = int(m[1]), int(m[2] if m[2] is not None else 1)
                # A count of 0 is a pure deletion: nothing on the new side to cover.
                changed.setdefault(path, set()).update(range(start, start + count))
    return changed


def evaluate(
    changed: dict[str, set[int]], report: dict[str, object]
) -> tuple[int, int, dict[str, list[int]]]:
    """Return (covered, executable, uncovered lines per file) over the changed lines."""
    files = report["files"]
    if not isinstance(files, dict):
        raise ValueError("the coverage report has no files table")
    covered = executable = 0
    uncovered: dict[str, list[int]] = {}
    for path, lines in changed.items():
        entry = files.get(path)
        if entry is None:
            continue
        hit = lines & set(entry["executed_lines"])
        miss = lines & set(entry["missing_lines"])
        covered += len(hit)
        executable += len(hit) + len(miss)
        if miss:
            uncovered[path] = sorted(miss)
    return covered, executable, uncovered


def ranges(numbers: list[int]) -> str:
    out: list[str] = []
    start = prev = numbers[0]
    for n in [*numbers[1:], None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        out.append(str(start) if start == prev else f"{start}-{prev}")
        if n is not None:
            start = prev = n
    return ", ".join(out)


def git_diff(base: str) -> str:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-c", "core.quotepath=off", *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    # Diffing from the merge base leaves out commits that landed on the base later.
    fork = git("merge-base", base, "HEAD").strip()
    return git(
        "diff",
        "-U0",
        "-M",
        "--no-color",
        "--no-ext-diff",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        fork,
        "--",
        "backend",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--base", required=True, help="base commit or branch to diff against"
    )
    ap.add_argument("--coverage", default="coverage.json", type=Path)
    ap.add_argument(
        "--threshold",
        default=90.0,
        type=float,
        help="percent of changed executable lines",
    )
    args = ap.parse_args(argv)
    try:
        report = json.loads(args.coverage.read_text())
        changed = {p: n for p, n in parse_diff(git_diff(args.base)).items() if n}
        files = report["files"]
        missing = [p for p in changed if p not in files]
        if changed and len(missing) == len(changed):
            names = ", ".join(sorted(missing))
            raise ValueError(
                f"no changed backend file is in the coverage report: {names}"
            )
        covered, executable, uncovered = evaluate(changed, report)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"changed-lines coverage: cannot run: {exc!r}", file=sys.stderr)
        return 2
    if executable == 0:
        print("changed-lines coverage: no changed backend lines")
        return 0
    pct = 100 * covered / executable
    print(
        f"changed-lines coverage: {covered}/{executable} executable changed lines "
        f"covered ({pct:.1f}%), threshold {args.threshold:g}%"
    )
    if pct >= args.threshold:
        return 0
    for path, lines in uncovered.items():
        print(f"  {path}: {ranges(lines)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
