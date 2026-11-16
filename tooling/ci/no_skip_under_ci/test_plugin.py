from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

HERE = Path(__file__).resolve().parent

CASES = {
    "skip": 'import pytest\n\ndef test_a():\n    pytest.skip("later")\n',
    "skip marker": "import pytest\n\n@pytest.mark.skip\ndef test_a(): ...\n",
    "xfail": "import pytest\n\n@pytest.mark.xfail\ndef test_a():\n    assert False\n",
    "skipped module": 'import pytest\n\npytest.skip("no", allow_module_level=True)\n',
}


def _run(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    ci: str | None,
) -> pytest.RunResult:
    pytester.makepyfile(test_tiny=source)
    monkeypatch.delenv("CI", raising=False)
    if ci is not None:
        monkeypatch.setenv("CI", ci)
    monkeypatch.setenv("PYTHONPATH", str(HERE.parent))
    return pytester.runpytest_subprocess(
        "-p",
        "no_skip_under_ci.plugin",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:randomly",
        "-p",
        "no:django",
    )


@pytest.mark.parametrize("source", CASES.values(), ids=CASES.keys())
def test_a_skip_fails_under_ci(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    result = _run(pytester, monkeypatch, source, "true")
    assert result.ret != 0, result.stdout.str()
    assert "no skips or xfail allowed under CI" in result.stdout.str()


@pytest.mark.parametrize("source", CASES.values(), ids=CASES.keys())
def test_a_skip_stays_a_skip_locally(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    result = _run(pytester, monkeypatch, source, None)
    assert result.ret in (0, 5), result.stdout.str()  # 5: no tests collected
    assert "allowed under CI" not in result.stdout.str()


def test_a_passing_test_passes_under_ci(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _run(pytester, monkeypatch, "def test_a(): ...\n", "true")
    assert result.ret == 0, result.stdout.str()
