import json
from pathlib import Path

import pytest

from grader_check.anchors import AnchorSetError, load_anchor_set, parse_anchor_set
from grader_check.grader import StubGrader
from grader_check.runner import PLACEHOLDER, main, run

FAILING = PLACEHOLDER.parent / "placeholder-failing"
NAMES = [
    "exact_level",
    "within_one_level",
    "no_inversion",
    "consistency",
    "rule_checks",
    "gaming_resistance",
    "injection_resistance",
]


def test_placeholder_set_passes_and_report_lists_every_threshold(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.json"
    assert main(["--report", str(report_path)]) == 0
    report = json.loads(report_path.read_text())
    assert report["passed"] is True
    assert [row["name"] for row in report["thresholds"]] == NAMES
    for row in report["thresholds"]:
        assert set(row) >= {"name", "value", "target", "passed"}


def test_failing_placeholder_set_fails_every_threshold(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    assert main(["--anchors", str(FAILING), "--report", str(report_path)]) == 1
    report = json.loads(report_path.read_text())
    assert report["passed"] is False
    assert [row["passed"] for row in report["thresholds"]] == [False] * 7


def test_rule_rejected_text_never_reaches_the_grader() -> None:
    anchor_set = parse_anchor_set(
        {
            "name": "t",
            "version": "1",
            "tasks": [
                {
                    "id": "w",
                    "skill": "writing",
                    "task_type": "task_1",
                    "prompt": "p",
                    "min_words": 5,
                    "max_words": 10,
                }
            ],
            "anchors": [
                {"id": "short", "task": "w", "level": "B1", "text": "Trop court"}
            ],
            "gaming_cases": [
                {
                    "id": "g",
                    "task": "w",
                    "kind": "off_topic",
                    "max_level": "A1",
                    "text": "un deux",
                }
            ],
        }
    )
    stub = StubGrader({})
    report = run(anchor_set, stub, repeats=2)
    assert stub.requests == []
    assert report["passed"] is False


def test_missing_anchor_set_exits_with_a_config_error(tmp_path: Path) -> None:
    assert main(["--anchors", str(tmp_path), "--report", str(tmp_path / "r")]) == 2


def test_repeats_below_two_is_refused() -> None:
    with pytest.raises(SystemExit):
        main(["--repeats", "1"])


def test_anchor_set_rejects_unknown_level_and_duplicate_ids() -> None:
    data = json.loads((PLACEHOLDER / "anchors.json").read_text())
    data["anchors"][0]["level"] = "B3"
    with pytest.raises(AnchorSetError, match="B3"):
        parse_anchor_set(data)
    data = json.loads((PLACEHOLDER / "anchors.json").read_text())
    data["anchors"].append(data["anchors"][0])
    with pytest.raises(AnchorSetError, match="duplicate"):
        parse_anchor_set(data)


def test_placeholder_sets_load() -> None:
    assert load_anchor_set(PLACEHOLDER).name == "placeholder"
    assert load_anchor_set(FAILING).name == "placeholder-failing"
