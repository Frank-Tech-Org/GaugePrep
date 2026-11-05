import json
import os
import subprocess
from pathlib import Path

import changed_lines_coverage as clc
import pytest


# Git hooks export GIT_DIR and friends; without this the temp repos below
# would run their git commands against the real checkout.
@pytest.fixture(autouse=True)
def clean_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)


def diff_for(path: str, *hunks: str) -> str:
    head = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
    return head + "".join(f"@@ {h} @@\n" for h in hunks)


def report(path: str, executed: list[int], missing: list[int]) -> dict[str, object]:
    return {"files": {path: {"executed_lines": executed, "missing_lines": missing}}}


def score(diff: str, rep: dict[str, object]) -> tuple[int, int, dict[str, list[int]]]:
    return clc.evaluate(clc.parse_diff(diff), rep)


def test_below_threshold_lists_the_uncovered_lines() -> None:
    diff = diff_for("backend/a.py", "-0,0 +1,10")
    covered, executable, uncovered = score(
        diff, report("backend/a.py", list(range(1, 9)), [9, 10])
    )
    assert (covered, executable) == (8, 10)
    assert 100 * covered / executable < 90
    assert uncovered == {"backend/a.py": [9, 10]}


def test_exactly_at_threshold_passes() -> None:
    diff = diff_for("backend/a.py", "-0,0 +1,10")
    covered, executable, _ = score(
        diff, report("backend/a.py", list(range(1, 10)), [10])
    )
    assert 100 * covered / executable == 90


def test_no_changed_lines() -> None:
    assert clc.parse_diff("") == {}
    assert score("", report("backend/a.py", [1], [2])) == (0, 0, {})


def test_deleted_only_hunk_has_no_lines_to_cover() -> None:
    diff = diff_for("backend/a.py", "-5,3 +4,0")
    assert clc.parse_diff(diff) == {"backend/a.py": set()}
    assert score(diff, report("backend/a.py", [1], [4])) == (0, 0, {})


def test_blank_comment_and_unmeasured_lines_do_not_count() -> None:
    diff = diff_for("backend/a.py", "-0,0 +1,3") + diff_for(
        "backend/tests/t.py", "-0,0 +1,2"
    )
    # Line 2 is a comment: in neither list. The tests file is omitted from the report.
    assert score(diff, report("backend/a.py", [1, 3], [])) == (2, 2, {})


def test_single_line_hunk_has_an_implied_count_of_one() -> None:
    assert clc.parse_diff(diff_for("backend/a.py", "-7 +7")) == {"backend/a.py": {7}}


def test_files_outside_backend_python_are_ignored() -> None:
    diff = diff_for("apps/web/x.py", "-0,0 +1,2") + diff_for(
        "backend/readme.md", "-0,0 +1,2"
    )
    assert clc.parse_diff(diff) == {}


def test_ranges_collapse_runs() -> None:
    assert clc.ranges([1, 2, 3, 7, 9, 10]) == "1-3, 7, 9-10"


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_renamed_file_counts_only_its_edited_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "backend").mkdir()
    old = tmp_path / "backend" / "old.py"
    old.write_text("".join(f"x{i} = {i}\n" for i in range(1, 11)))
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "mv", "backend/old.py", "backend/new.py")
    new = tmp_path / "backend" / "new.py"
    new.write_text(new.read_text().replace("x4 = 4", "x4 = 40"))
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "rename and edit line 4")
    (tmp_path / "coverage.json").write_text(
        json.dumps(report("backend/new.py", list(range(1, 11)), []))
    )
    monkeypatch.chdir(tmp_path)
    assert clc.parse_diff(clc.git_diff("HEAD~1")) == {"backend/new.py": {4}}
    assert clc.main(["--base", "HEAD~1"]) == 0


def test_main_fails_and_names_uncovered_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "backend").mkdir()
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    (tmp_path / "backend" / "a.py").write_text("a = 1\nb = 2\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "add")
    (tmp_path / "coverage.json").write_text(
        json.dumps(report("backend/a.py", [1], [2]))
    )
    monkeypatch.chdir(tmp_path)
    assert clc.main(["--base", "HEAD~1"]) == 1
    out = capsys.readouterr().out
    assert "backend/a.py: 2" in out
    assert "1/2" in out


def test_no_changed_backend_lines_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    (tmp_path / "README.md").write_text("hi\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "docs")
    (tmp_path / "coverage.json").write_text(json.dumps({"files": {}}))
    monkeypatch.chdir(tmp_path)
    assert clc.main(["--base", "HEAD~1"]) == 0
    assert "no changed backend lines" in capsys.readouterr().out


def repo_with_change(tmp_path: Path, name: str = "a.py") -> Path:
    (tmp_path / "backend").mkdir()
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    (tmp_path / "backend" / name).write_text("a = 1\nb = 2\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "add")
    return tmp_path


def run_main(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    report_text: str | None,
    base: str = "HEAD~1",
) -> tuple[int, str, str]:
    if report_text is not None:
        (repo / "coverage.json").write_text(report_text)
    monkeypatch.chdir(repo)
    code = clc.main(["--base", base])
    out, err = capsys.readouterr()
    return code, out, err


def test_missing_coverage_file_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = repo_with_change(tmp_path)
    code, _, err = run_main(repo, monkeypatch, capsys, None)
    assert code == 2
    assert "cannot run" in err and "FileNotFoundError" in err


def test_invalid_coverage_json_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = run_main(repo_with_change(tmp_path), monkeypatch, capsys, "{nope")
    assert code == 2
    assert "cannot run" in err


def test_unresolvable_base_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = repo_with_change(tmp_path)
    code, _, err = run_main(
        repo, monkeypatch, capsys, '{"files": {}}', base="nosuchref"
    )
    assert code == 2
    assert "cannot run" in err


@pytest.mark.parametrize(
    "text",
    ["{}", '{"files": []}', '{"files": {"backend/a.py": {"missing_lines": [2]}}}'],
)
def test_malformed_report_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    text: str,
) -> None:
    code, _, err = run_main(repo_with_change(tmp_path), monkeypatch, capsys, text)
    assert code == 2
    assert "cannot run" in err


def test_changed_file_missing_from_report_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = repo_with_change(tmp_path)
    code, _, err = run_main(
        repo, monkeypatch, capsys, '{"files": {"backend/other.py": {}}}'
    )
    assert code == 2
    assert "backend/a.py" in err


def test_tests_only_change_still_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    (tmp_path / "backend" / "tests" / "t.py").write_text("a = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "add")
    code, _, _ = run_main(tmp_path, monkeypatch, capsys, '{"files": {}}')
    assert code == 0


def test_added_line_starting_with_plus_plus_does_not_end_the_file() -> None:
    diff = (
        "diff --git a/backend/a.py b/backend/a.py\n"
        "--- a/backend/a.py\n+++ b/backend/a.py\n"
        "@@ -0,0 +1,2 @@\n+x = 1\n+++ y\n"
        "@@ -9,0 +10,1 @@\n+z = 2\n"
    )
    assert clc.parse_diff(diff) == {"backend/a.py": {1, 2, 10}}


def test_path_with_a_space(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = repo_with_change(tmp_path, "my file.py")
    text = json.dumps(report("backend/my file.py", [1], [2]))
    code, out, _ = run_main(repo, monkeypatch, capsys, text)
    assert code == 1
    assert "backend/my file.py: 2" in out


def test_quoted_path_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = repo_with_change(tmp_path, 'q"x.py')
    code, _, err = run_main(repo, monkeypatch, capsys, '{"files": {}}')
    assert code == 2
    assert "quoted path" in err


def test_one_changed_file_absent_from_report_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = repo_with_change(tmp_path)
    (repo / "backend" / "b.py").write_text("c = 3\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "second file")
    text = json.dumps(report("backend/a.py", [1, 2], []))
    code, _, err = run_main(repo, monkeypatch, capsys, text, base="HEAD~2")
    assert code == 2
    assert "backend/b.py" in err


def test_only_the_backend_tests_directory_is_unmeasured() -> None:
    def changed(path: str) -> dict[str, set[int]]:
        diff = (
            f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -0,0 +1 @@\n"
        )
        return clc.parse_diff(diff)

    assert changed("backend/tests/t.py") == {}
    assert changed("backend/modules/x/migrations/0001_a.py") == {}
    assert changed("backend/modules/x/tests/t.py") != {}
