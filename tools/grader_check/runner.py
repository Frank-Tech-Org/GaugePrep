import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from grader_check import checks
from grader_check.anchors import AnchorSet, AnchorSetError, Task, load_anchor_set
from grader_check.grader import Grader, StubGrader, build_request, grade
from grader_check.rules import check_rules

PLACEHOLDER = Path(__file__).resolve().parent / "anchors" / "placeholder"


def _grade_text(grader: Grader, case_id: str, task: Task, text: str) -> str | None:
    if check_rules(task, text) != "accept":
        return None
    return grade(grader, build_request(case_id, task, text))


def run(anchor_set: AnchorSet, grader: Grader, repeats: int) -> dict[str, Any]:
    tasks = anchor_set.tasks
    runs = {
        a.id: [_grade_text(grader, a.id, tasks[a.task], a.text) for _ in range(repeats)]
        for a in anchor_set.anchors
    }
    first = [(a, runs[a.id][0]) for a in anchor_set.anchors]
    pairs = [(a.level, got) for a, got in first]

    rule_outcomes = [
        (r.expected, check_rules(tasks[r.task], r.text)) for r in anchor_set.rule_cases
    ]
    gaming = [
        (g.id, g.kind, g.max_level, _grade_text(grader, g.id, tasks[g.task], g.text))
        for g in anchor_set.gaming_cases
    ]
    injection = [
        (
            i.id,
            _grade_text(grader, i.id, tasks[i.task], i.text),
            _grade_text(grader, f"{i.id}:injected", tasks[i.task], i.injected_text),
        )
        for i in anchor_set.injection_cases
    ]

    results = [
        checks.exact_level(pairs),
        checks.within_one_level(pairs),
        checks.no_inversion([(a.id, a.task, a.level, got) for a, got in first]),
        checks.consistency(runs),
        checks.rule_checks(rule_outcomes),
        checks.gaming_resistance(gaming),
        checks.injection_resistance(injection),
    ]
    return {
        "anchor_set": anchor_set.name,
        "anchor_set_version": anchor_set.version,
        "grader": grader.name,
        "repeats": repeats,
        "passed": all(r.passed for r in results),
        "thresholds": [r.as_dict() for r in results],
    }


def _load_stub(directory: Path) -> StubGrader:
    path = directory / "stub_replies.json"
    try:
        replies = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AnchorSetError(f"{path} not found; the stub grader needs it") from exc
    return StubGrader(replies)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="grader_check", description="Run the grader release check."
    )
    parser.add_argument(
        "--anchors",
        type=Path,
        default=PLACEHOLDER,
        help="anchor set directory (default: the placeholder set)",
    )
    parser.add_argument("--report", type=Path, default=Path("grader-check-report.json"))
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    if args.repeats < 2:
        parser.error("--repeats must be at least 2 to measure consistency")

    try:
        anchor_set = load_anchor_set(args.anchors)
        report = run(anchor_set, _load_stub(args.anchors), args.repeats)
    except (AnchorSetError, KeyError, json.JSONDecodeError) as exc:
        print(f"grader check could not run: {exc}", file=sys.stderr)
        return 2

    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in report["thresholds"]:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f"{mark}  {row['name']}: {row['value']} (target {row['target']})")
    print(f"{'passed' if report['passed'] else 'FAILED'}; report at {args.report}")
    return 0 if report["passed"] else 1
