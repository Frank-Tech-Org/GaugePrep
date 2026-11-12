# Grader release check

A new grader version (model, prompt, rubric, anchor set or settings) serves learners only after it passes this check. The runner grades an anchor set, scores the results against seven thresholds, writes a JSON report and exits non-zero if any threshold is missed.

Right now it runs a **stub grader** on a **placeholder anchor set**. The stub makes no model call: it answers from a script, so the checks and the CI wiring can be tested before the real grader and anchors exist.

## Run it

From the repository root (Python 3.14, standard library only):

```bash
PYTHONPATH=tooling/ci python -m grader_check                       # placeholder set, should pass
PYTHONPATH=tooling/ci python -m grader_check \
  --anchors tooling/ci/grader_check/anchors/placeholder-failing    # fails every threshold
```

Options: `--anchors DIR` (default: the placeholder set), `--report FILE` (default `grader-check-report.json`), `--repeats N` (runs per anchor for the consistency check, default 3, minimum 2).

Exit codes: `0` all thresholds met, `1` at least one missed, `2` the anchor set or stub replies could not be loaded.

In CI the workflow runs on pull requests that change the grader files or this tool, and uploads the report as the `grader-check-report` artifact. A manual run can choose the `placeholder-failing` set to show the workflow going red.

## Thresholds

| Name | Passes when |
|---|---|
| `exact_level` | at least 60% of anchors get their exact level |
| `within_one_level` | at least 95% are within one level |
| `no_inversion` | a lower-level anchor never scores above a higher-level one for the same task |
| `consistency` | at least 90% of repeated runs give the anchor's most common level |
| `rule_checks` | 100% of rule-check cases get the expected outcome |
| `gaming_resistance` | keyword-stuffed, template and off-topic texts are never rated above their cap, and all three kinds are present |
| `injection_resistance` | a response with a hidden instruction gets the same level as without it |

Any check with nothing to score fails. Each report row has `name`, `description`, `value`, `target`, `passed` and `detail`.

A grader output that isn't valid JSON matching `{"level": "<A1..C2>", "evidence": [...]}` is retried once, then flagged (counted as a miss). A text that fails a rule (task type, word range) is never sent to the grader.

## Adding the real anchor set

1. Create a directory for it, for example `tooling/ci/grader_check/anchors/tcf-writing-v1/`, with an `anchors.json` in the same shape as `anchors/placeholder/anchors.json`:
   - `name`, `version`
   - `tasks`: `id`, `skill` (`writing` or `speaking`), `task_type` (`task_1` to `task_3`), `prompt`, `min_words`, `max_words` (null for speaking)
   - `anchors`: `id`, `task`, `level` (the agreed human level, A1 to C2), `text`
   - `rule_cases`: `id`, `task`, `text`, `expected` (`accept`, `reject_word_range` or `reject_task_type`)
   - `gaming_cases`: `id`, `task`, `kind` (`keyword_stuffing`, `template` or `off_topic`), `max_level`, `text`
   - `injection_cases`: `id`, `task`, `text`, `injected_text` (the same response with an instruction hidden in it)
2. Cover every level for each task. The no-inversion check only compares anchors of the same task, so each task needs at least two levels.
3. Anchors hold learner texts only: no names, emails or phone numbers. Strip them before adding a text.
4. Bump `version` on any change; the version is part of the grader version and goes in the report.
5. Point the workflow at the new directory (the `--anchors` argument) and add its path to the workflow's `paths` trigger if it lives outside this tool.

`stub_replies.json` belongs to the stub only. A real anchor set doesn't need one once the stub is replaced by the real grader, which plugs in through the `Grader` protocol in `grader.py` (one `complete(request)` call returning the raw model output). `build_request` already puts the task prompt and learner text inside delimiter tags, escaped so a response can't close its own tag; keep using it.

## Grader files and the trigger

The workflow runs when a pull request changes `apps/backend/modules/assessment/grader/**` or this tool. The grader's prompt, rubric and model settings should live under that path when they are written; if they land elsewhere, add the path to the workflow trigger.

The CEFR level list and the rule checks live here for now because `examcore` doesn't define them yet. Move them to `examcore` when it does and import them from there.
