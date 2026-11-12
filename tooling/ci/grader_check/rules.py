# Deterministic checks that run before any grader call. A response that fails one
# is never sent to the model. Move to examcore with the real exam rules.
import re

from grader_check.anchors import Task

TASK_TYPES = {
    "writing": frozenset({"task_1", "task_2", "task_3"}),
    "speaking": frozenset({"task_1", "task_2", "task_3"}),
}

_WORD = re.compile(r"\w+(?:['’-]\w+)*")


def count_words(text: str) -> int:
    return len(_WORD.findall(text))


def check_rules(task: Task, text: str) -> str:
    if task.task_type not in TASK_TYPES.get(task.skill, frozenset()):
        return "reject_task_type"
    words = count_words(text)
    if task.min_words is not None and words < task.min_words:
        return "reject_word_range"
    if task.max_words is not None and words > task.max_words:
        return "reject_word_range"
    return "accept"
