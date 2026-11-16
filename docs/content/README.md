# Content production kit

This kit tells authoring agents, reviewing agents and human reviewers how to produce every piece of release 1 content: listening and reading items, writing prompts, speaking tasks, simulation forms, curriculum lessons and free-track vocabulary. Anchors for the grader follow their own protocol, which comes with the grader work; the counts and rater rules are already in the spec's calibration section.

The rules here apply the TCF Canada exam specification (`docs/exam-specs/TCF-Canada.md`, cited below as "spec") and the PRD. When this kit and the spec disagree, the spec wins and this kit must be corrected.

## 1. Files in this kit

| File | Purpose |
|---|---|
| `README.md` | Workflow, roles, batches, statuses, volumes and the human review plan (this file) |
| `authoring-guide.md` | How to write each item and task type, level by level |
| `audio-script-rules.md` | Script markup, voice bank, speech rates, audio checks |
| `review-checklist.md` | What the reviewing agent and the human reviewer check, defect codes and acceptance rules |
| `originality-and-sources.md` | What may and may not be used as a source, licences, copying checks |
| `curriculum-map.md` | The 50 units of the French curriculum (A1 to C1) and their goals |
| `vocabulary-themes.md` | The 60 free-track vocabulary themes |
| `schemas/` | JSON Schemas, one per content type |
| `examples/` | One valid file per content type |

The validator that authors run before a pull request and CI runs on every content change is not in the repository yet; it has its own ticket. Until it lands, check files against the schemas by hand or with any JSON Schema 2020-12 tool.

## 2. Where content lives

Content is authored as JSON files in the repository, under `content/`, one file per version:

```
content/
  tcf-ca/
    listening/TCF-CA-CO-L4-0001-v1.json
    reading/TCF-CA-CE-R5-0001-v1.json
    writing/TCF-CA-EE-EE3-0001-v1.json
    speaking/TCF-CA-EO-EO2-0001-v1.json
    forms/TCF-CA-FORM-0001-v1.json
  fr-curriculum/B1/FR-CUR-B1-U04-L2-v1.json
  fr-vocabulary/transport/FR-VOC-transport-0001-v1.json
  batches/BATCH-0007.yml
```

- The file name is `<code>-v<version>.json`. A published version is never edited: a correction is a new file with the next version number.
- CI will run the content validator on every changed file once it lands.
- An import command (`manage.py content_import`) loads approved files into the `content` module as versions with status "approved". Publication then happens in the internal console, where the audit log records who published what (PRD CMS-2, CMS-8). The database stays the source of truth for what learners see; the repository is the authoring workspace. [ADR-025](../adr/ADR-025-content-as-validated-files.md) records this decision.
- Audio files are not stored in Git. The media job produces them from the scripts after approval (spec 10.2 step 4).

## 3. Roles

| Role | Who | Does |
|---|---|---|
| Author | Authoring agent | Drafts items in batches from a batch brief, runs the validator, opens a pull request |
| Reviewing agent | A different agent from the author, with the review checklist as its instructions | Reviews every item in the batch against `review-checklist.md`, records a verdict per item, sends defects back |
| Human reviewer | Frank or a French-language reviewer he appoints (PRD role "content reviewer") | Reviews a random sample of every batch, all simulation-form items, all anchors and the audio listening checks; approves or rejects the batch |
| Audio producer | Media job plus a human listener | Voices scripts, runs automatic checks, a human listens (Section 7) |
| Form builder | Form builder tool (PRD CMS-5) | Assembles simulation forms from published items under spec 7.2 |

An agent never approves its own work, and no batch is approved without the human sample review. This keeps the PRD rule "publication requires reviewer approval" (PRD Section 11) true when most drafting and first-line review is done by agents.

## 4. Workflow

Each step maps to spec 10.2.

1. **Brief.** The PM agent opens a batch issue from the coverage report (Section 6). A batch is 20 to 40 items of one type, or one curriculum unit, or one vocabulary theme. The brief file `content/batches/BATCH-nnnn.yml` lists: type, target levels with counts, themes, focus mix, voice and accent mix for listening, and the codes reserved for the batch.
2. **Draft.** The author drafts every item following `authoring-guide.md`, fills `authoring` honestly (including `drafted_with_ai` and the model ID), runs the validator and opens a pull request with status "in review".
3. **Agent review.** The reviewing agent checks every item and writes its verdict in the pull request as a table: code, verdict (accept, revise, reject), defect codes, comment. Items marked "revise" go back to the author; two rejections of the same item end it.
4. **Human sample review.** When the reviewing agent accepts the whole batch, the human reviewer reviews the sample defined in Section 5 and records the result in the batch issue. The batch is approved, or returned with the defects found.
5. **Merge and import.** The approved pull request is merged; the import command loads the versions as "approved".
6. **Audio.** For listening items, lessons with audio input and vocabulary entries, the media job voices the scripts and runs the automatic checks; the human listening check follows Section 7.
7. **Publish.** The human reviewer publishes the batch in the console. Publication assigns the initial difficulty from the target level plus the reviewer-confirmed adjustment (spec 8.1).
8. **Monitor.** Item statistics and learner flags (PRD CMS-7) create revision issues.

## 5. Human review plan

AI drafting is fast, but a model that drafted an item cannot be trusted to judge its level or catch its own ambiguity, and a second model shares many of the same blind spots. Humans therefore check a sample of everything and all of the high-stakes content.

| Content | Human review |
|---|---|
| Items, prompts and tasks used in simulation forms | 100% before the form is published |
| Other listening and reading items, writing prompts, speaking tasks | Random sample of 10% of each batch, at least 5 items |
| Curriculum lessons | 1 lesson in every 4 (one per unit), chosen at random |
| Vocabulary entries | Random sample of 5% of each theme, at least 5 entries |
| Anchors | 100%, under the anchor protocol |
| Listening audio | Section 7 |

Acceptance rule for a sample:

- Any **critical** defect (wrong key, two defensible answers, offensive or unfair content, copied or closely paraphrased text, wrong level by two or more levels) sends the whole batch back for a full agent re-review, and a new sample of twice the size is drawn.
- **Major** defects (level off by one, implausible distractor, unnatural French, rule of the guide broken) in more than 1 item per 10 sampled send the batch back the same way.
- **Minor** defects (typography, small wording) are fixed by the author and do not block approval.

Defect codes and their severity are defined in `review-checklist.md`.

**Estimated human time for release 1:** about 13 hours for the 390 simulation-form items, 4 hours for sampled items and prompts, 6 hours for sampled lessons, 2 hours for vocabulary, and the listening check of Section 7. Anchors are planned separately in the anchor protocol.

## 6. Volumes and coverage

Release 1 volumes come from spec 10.1 and PRD Section 11.

| Content | Total | By level or split |
|---|---|---|
| Listening items | 600 | A1 80, A2 100, B1 120, B2 130, C1 100, C2 70 |
| Reading items | 600 | A1 80, A2 100, B1 120, B2 130, C1 100, C2 70 |
| Writing prompts | 120 | 40 per task type, every theme present in every task type |
| Speaking EO1 sets | 30 | 8 to 10 questions each |
| Speaking EO2 cards | 40 | With examiner facts and a complication |
| Speaking EO3 questions | 60 | With 3 follow-ups each |
| Simulation forms | 5 | Built after the banks reach the volumes above |
| Curriculum lessons | 200 | A1 to C1, 10 units per level, 4 lessons per unit |
| Vocabulary entries | About 3,000 | 60 themes, A1 to B2 |

Item types per level follow the spec blueprint (7.1). Within a level, split items across the allowed types so that every type has enough items for practice filters and for five forms: for example, B1 listening items are split roughly evenly between L3, L4 and L5.

The coverage report (`manage.py content_coverage`, built in M1) counts published and in-progress items by paper, type, level, theme and focus, and lists gaps against these targets. Batch briefs are always created from its gaps.

Focus mix for listening and reading, per level:

| Level | Focus mix |
|---|---|
| A1, A2 | Mostly detail and purpose; some main idea |
| B1 | Main idea and detail about equal; some inference and purpose |
| B2 | At least half inference, attitude, purpose or structure (spec 4.2 for reading; apply the same to listening) |
| C1, C2 | Mostly inference, attitude, structure and vocabulary in context |

## 7. Listening audio check

Spec 3.2 requires a human listener to approve every listening audio file before publication. To keep that affordable, the media job runs automatic checks first, so that the listener only judges what a machine cannot:

1. **Automatic checks on every file:** transcribe the generated audio with the batch speech recognition service and compare it with the script (word error rate at most 3% after normalisation); duration within the type's range (spec 3.1); measured words per minute within 10% of `target_wpm`; loudness normalised to -16 LUFS with no clipping. A file that fails is regenerated, at most three times, then sent to the human with the failure.
2. **Human listening on every listening item:** naturalness, pronunciation of names and numbers, the key information clearly audible, background sound not masking it. About 1 minute per item including replay, so about 10 hours for 600 items, spread over the batches.
3. **Lesson audio and vocabulary audio:** automatic checks on every file, human listening on the same sample as the text review (Section 5).

## 8. Statuses

The status values are those of PRD CMS-2 and spec 10.3: `draft`, `in_review`, `approved`, `published`, `retired`. In the repository, a file is `draft` until its pull request is opened, `in_review` until the batch is approved, then `approved` when imported. `published` and `retired` exist only in the database.

## 9. Content agent instructions in one page

For agents that load only one file before drafting, the minimum rules are:

1. Read the batch brief, the relevant section of `authoring-guide.md`, and the example file of the type.
2. Write original French only. Never copy, translate or closely paraphrase FEI papers, sample items, published subjects or any other exam material (`originality-and-sources.md`).
3. One correct answer; three plausible, clearly wrong distractors; key letters balanced within the batch.
4. Stay inside the type's level range, length range and the level's language controls.
5. Fill every field truthfully, including `drafted_with_ai` and the model.
6. Run the content validator on your folder and fix every failure before opening the pull request (the validator comes with its own ticket; until then, check against the schemas).
