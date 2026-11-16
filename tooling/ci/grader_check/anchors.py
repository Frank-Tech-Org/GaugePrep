import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from grader_check.levels import LEVELS

_SET = "anchor set"
RULE_OUTCOMES = ("accept", "reject_word_range", "reject_task_type")
GAMING_KINDS = ("keyword_stuffing", "template", "off_topic")


class AnchorSetError(ValueError):
    pass


@dataclass(frozen=True)
class Task:
    id: str
    skill: str
    task_type: str
    prompt: str
    min_words: int | None
    max_words: int | None


@dataclass(frozen=True)
class Anchor:
    id: str
    task: str
    level: str
    text: str


@dataclass(frozen=True)
class RuleCase:
    id: str
    task: str
    text: str
    expected: str


@dataclass(frozen=True)
class GamingCase:
    id: str
    task: str
    kind: str
    text: str
    max_level: str


@dataclass(frozen=True)
class InjectionCase:
    id: str
    task: str
    text: str
    injected_text: str


@dataclass(frozen=True)
class AnchorSet:
    name: str
    version: str
    tasks: dict[str, Task]
    anchors: tuple[Anchor, ...]
    rule_cases: tuple[RuleCase, ...]
    gaming_cases: tuple[GamingCase, ...]
    injection_cases: tuple[InjectionCase, ...]


def _field(item: dict[str, Any], key: str, where: str) -> Any:
    if key not in item:
        raise AnchorSetError(f"{where}: missing '{key}'")
    return item[key]


def _choice(value: str, allowed: Iterable[str], where: str) -> str:
    allowed = tuple(allowed)
    if value not in allowed:
        raise AnchorSetError(f"{where}: '{value}' is not one of {', '.join(allowed)}")
    return value


def parse_anchor_set(data: dict[str, Any]) -> AnchorSet:
    tasks = {}
    for t in _field(data, "tasks", _SET):
        where = f"task {t.get('id')}"
        task_id = _field(t, "id", where)
        tasks[task_id] = Task(
            id=task_id,
            skill=_field(t, "skill", where),
            task_type=_field(t, "task_type", where),
            prompt=_field(t, "prompt", where),
            min_words=t.get("min_words"),
            max_words=t.get("max_words"),
        )

    seen: set[str] = set()

    def case(item: dict[str, Any], kind: str) -> tuple[str, str, str]:
        where = f"{kind} {item.get('id')}"
        case_id = _field(item, "id", where)
        if case_id in seen:
            raise AnchorSetError(f"{where}: duplicate id")
        seen.add(case_id)
        _choice(_field(item, "task", where), tasks, where)
        return where, case_id, item["task"]

    anchors = []
    for a in _field(data, "anchors", _SET):
        where, case_id, task = case(a, "anchor")
        level = _choice(_field(a, "level", where), LEVELS, where)
        anchors.append(Anchor(case_id, task, level, _field(a, "text", where)))

    rule_cases = []
    for r in data.get("rule_cases", []):
        where, case_id, task = case(r, "rule case")
        expected = _choice(_field(r, "expected", where), RULE_OUTCOMES, where)
        rule_cases.append(RuleCase(case_id, task, _field(r, "text", where), expected))

    gaming_cases = []
    for g in data.get("gaming_cases", []):
        where, case_id, task = case(g, "gaming case")
        gaming_cases.append(
            GamingCase(
                case_id,
                task,
                _choice(_field(g, "kind", where), GAMING_KINDS, where),
                _field(g, "text", where),
                _choice(_field(g, "max_level", where), LEVELS, where),
            )
        )

    injection_cases = []
    for i in data.get("injection_cases", []):
        where, case_id, task = case(i, "injection case")
        injection_cases.append(
            InjectionCase(
                case_id,
                task,
                _field(i, "text", where),
                _field(i, "injected_text", where),
            )
        )

    return AnchorSet(
        name=_field(data, "name", _SET),
        version=str(_field(data, "version", _SET)),
        tasks=tasks,
        anchors=tuple(anchors),
        rule_cases=tuple(rule_cases),
        gaming_cases=tuple(gaming_cases),
        injection_cases=tuple(injection_cases),
    )


def load_anchor_set(directory: Path) -> AnchorSet:
    path = directory / "anchors.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AnchorSetError(f"{path} not found") from exc
    except json.JSONDecodeError as exc:
        raise AnchorSetError(f"{path}: invalid JSON ({exc})") from exc
    return parse_anchor_set(data)
