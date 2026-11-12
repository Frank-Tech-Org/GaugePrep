from pathlib import Path

from shell_test_support import clean_env, run_script, stub

SHA = "a" * 40

PULLS = (
    '[{"number":7,"merged_at":"t","merge_commit_sha":"%s","base":{"ref":"develop"}}]'
)
INFO = '{"head":{"ref":"feature/187-x","sha":"h"},"merged_by":{"login":"boss"}}'

GH_STUB = f"""
echo "$*" >> "$STUB_DIR/gh.log"
case "$*" in
  "api repos/o/r/commits/$SHA/pulls") echo '{PULLS}' | sed "s/%s/$SHA/" ;;
  "api repos/o/r/pulls/7") echo '{INFO}' ;;
  "api repos/o/r/commits/$SHA --jq .files[].filename") echo "README.md" ;;
  "issue list"*|"issue create"*) ;;
  *) echo "unexpected gh call: $*" >&2; exit 9 ;;
esac
"""


def setup(tmp_path: Path, forced: str) -> dict[str, str]:
    stub_dir = tmp_path / "bin"
    stub(stub_dir, "gh", GH_STUB)
    env = clean_env(
        tmp_path,
        STUB_DIR=str(stub_dir),
        GH_TOKEN="t",
        REPO="o/r",
        EVENT="push",
        SHA=SHA,
        BRANCH="develop",
        ACTOR="someone",
        FORCED=forced,
        IN_BRANCH="",
        IN_SHA="",
        OWNER="boss",
    )
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    return env


def test_push_from_an_owner_merged_pull_request_is_allowed(tmp_path: Path) -> None:
    done = run_script("develop_alarm", tmp_path, setup(tmp_path, "false"))
    assert done.returncode == 0, done.stderr
    assert "issue create" not in (tmp_path / "bin" / "gh.log").read_text()


def test_forced_push_opens_an_issue_and_fails(tmp_path: Path) -> None:
    done = run_script("develop_alarm", tmp_path, setup(tmp_path, "true"))
    assert done.returncode == 1
    log = (tmp_path / "bin" / "gh.log").read_text()
    assert "issue create" in log
    assert "forced push" in log


def test_manual_run_with_a_bad_sha_is_refused(tmp_path: Path) -> None:
    env = setup(tmp_path, "false") | {
        "EVENT": "workflow_dispatch",
        "IN_SHA": "nope",
        "IN_BRANCH": "develop",
    }
    done = run_script("develop_alarm", tmp_path, env)
    assert done.returncode == 2
    assert "full commit id" in done.stderr
