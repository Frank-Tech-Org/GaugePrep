# ADR-026: Speech recognition chosen by a public-corpus benchmark

- Status: Accepted
- Date: 2026-11-12
- Supersedes: ADR-008

## Context

ADR-008 and section 8.6 chose the speech recognition provider in milestone 0 by recording 20 consenting Cameroonian speakers (francophone and anglophone, A2 to C1) on the three TCF speaking tasks, with verbatim human transcripts. That needs recruitment, signed consent, personal data handling and paid transcription before the voice examiner can start. On 2026-11-12 the owner closed the recruitment ticket and approved choosing the provider from public corpora instead.

The need has not changed: one provider serves live and batch transcription, nobody publishes accuracy on Central African French, and grading needs the learner's errors kept in the transcript rather than corrected. The release 1 launch criterion (at least 20 Cameroonian speakers, francophone and anglophone, transcripts accurate enough to grade on at least 90% of answers) is a launch gate, not a milestone 0 task, and stays.

## Options considered

- **Do nothing (keep ADR-008):** wait for 20 recruited speakers. Highest fidelity, but recruitment is closed, so the voice examiner (M4) and speaking grading have no provider and no date.
- **Self-host Whisper large-v3 everywhere, no comparison:** no vendor spend, and the open weights stay ours. It has no streaming mode, so the live examiner needs a chunking wrapper and a GPU server that the cost model and D-7 don't plan for. Whisper adds phrases that were never spoken in about 1% of transcripts, which is a grading risk. We'd still have no number on accented French. Undo: swap the adapter.
- **Public-corpus benchmark (chosen):** run the candidates on public accented and learner French, plus a synthetic planted-error set, under ADR-008's rule. Free within the providers' free allowances, a few days of work, no personal data. It says nothing about anglophone Cameroonians, spontaneous A2 to C1 speech or phone microphones on slow networks. Undo: rerun on new data; providers sit behind the speech-to-text interface.
- **Corpus plus 3 to 5 volunteers:** the corpus benchmark plus a handful of recorded volunteers for the anglophone Cameroonian gap. Not chosen; held as the fallback if the beta recruitment below finds no anglophone Cameroonians, because it is then the only route to any signal on them. Five speakers can't separate engines that sit within a WER point of each other, and it brings back the consent, transcription and data handling the owner just closed. The 20 consenting beta learners before launch cover the same gap with four times the speakers.

## Evidence

- OpenSLR 57, African Accented French: Apache-2.0, about 22 h, 232 speakers recorded in Cameroon (Yaoundé, 84), Gabon (CA16, 125 from Cameroon, Chad, Congo and Gabon) and Niger (23), mostly read prompts with transcripts. https://www.openslr.org/57/ ; listed as read speech in https://arxiv.org/abs/2601.05911
- Common Voice French: CC0, scripted speech with a self-reported accent field, and a separate small spontaneous speech set, now distributed through the Mozilla Data Collective. https://commonvoice.mozilla.org/en/datasets
- LANGSNAP French: British university learners of French, interviews and picture narratives with audio and CHAT transcripts. TalkBank data is CC BY-NC-SA 3.0 and may not be built into commercial products or models. https://talkbank.org/slabank/access/French/LANGSNAP6.html ; https://talkbank.org/0share/rules.html
- FLLOC: five corpora of instructed English-speaking learners of French, beginners to final-year undergraduates, CHAT transcripts, audio on request, CC BY-NC-SA 3.0 Unported. https://ota.bodleian.ox.ac.uk/repository/xmlui/handle/20.500.12024/2495 (now https://llds.ling-phil.ox.ac.uk/llds/xmlui/handle/20.500.14106/2495)
- Synthetic speech is no stand-in for real speakers: Whisper large-v3 scored 3.7% WER on synthetic child speech and 21.7% on real child speech (https://arxiv.org/abs/2603.25727, section 5), and TTS speech that recognisers find easy tends to "lose distinctive qualities like strong accent" (https://arxiv.org/abs/2410.16726). A planted error is still in the audio whatever the voice, so a synthetic set can test error preservation.
- Whisper large-v3: 30-second window, "cannot be used for real-time transcription out of the box" (https://huggingface.co/openai/whisper-large-v3); hallucinated phrases in about 1% of transcripts (https://arxiv.org/abs/2402.08021).
- Engines and free allowances, checked 2026-11-12: Deepgram Nova-3 monolingual French (`language=fr`), $200 credit for new accounts, $0.0048 a minute streaming and $0.0043 batch at list price (https://deepgram.com/pricing). ElevenLabs Scribe v3 at $0.20 an hour and Scribe v3 Live at $0.22, with 4 h 30 min batch and 2 h 30 min live a month free (https://elevenlabs.io/pricing/api). Speechmatics Enhanced: $100 free credit, no card at sign-up, French (`fr`, global accents) in batch and real time, per-word timing and confidence, $0.75 an hour batch and $0.80 real time (https://www.speechmatics.com/pricing, https://docs.speechmatics.com/speech-to-text/languages). Mistral Voxtral is dropped from the keyed engines: its free trial gives no API key (reported to me, not rechecked). Its open weights (Apache-2.0, French, Voxtral Mini 3B about 9.5 GB of GPU memory, Mini 4B Realtime 16 GB) need a GPU this machine lacks, and the model cards document no word timing or confidence, so it could not pass the selection rule anyway. Also checked 2026-11-13 and not added: Gladia (EUR 50 one-time credit, card at sign-up not stated, French on Solaria, per-word confidence not documented) and Groq (hosted Whisper large-v3 at $0.111 an hour, segment-level confidence only, and the same model as the control, so it can only repeat the control's result).

## Decision

The provider is chosen by a benchmark on public corpora, run once in milestone 0:

- Accented French: OpenSLR 57, with Cameroonian speakers kept as their own group in the results.
- Learner French from English speakers: LANGSNAP and FLLOC, for internal measurement only. Their audio and transcripts never enter the repository, a model, a prompt or the product, and only aggregate numbers are published. If TalkBank or Oxford refuse a company's evaluation use, that set is dropped and the claim below narrows to Central African French.
- Control: Common Voice French scripted and spontaneous speech.
- Error preservation: scripted learner sentences with planted grammatical errors, spoken by a synthetic voice. This set measures preservation only, never accent accuracy.
- Candidates, each streaming and batch: Deepgram Nova-3 (monolingual French), ElevenLabs Scribe v3 Live and Scribe v3, Speechmatics Enhanced (batch only so far). Whisper large-v3 runs as a control and cannot win.
- A fixed, seeded subset sized to stay inside each provider's free allowance; any paid spend goes to the owner first.
- One text normaliser for every engine; results by corpus and speaker code only.

ADR-008's rule picks the winner, unchanged: the lowest word error rate among candidates that preserve at least 95% of the learner's errors and return word-level timing and confidence; within one point of word error rate, the cheaper wins. Latency and price per audio hour are measured and reported.

Public wording is "tested on Central African and English-speaking learner French". We make no claim for anglophone Cameroonians, spontaneous A2 to C1 speech, or phone microphones on slow networks.

## Results

Run 2026-11-13 with `tooling/asr_benchmark` (seed 15, batch mode, one normaliser for every engine; the streaming harness has not run live). Only Whisper large-v3 has run: the other three engines are skipped until their API keys exist, so no provider is chosen yet.

| Engine | WER Common Voice FR (%) | WER OpenSLR 57 Cameroon (%) | WER OpenSLR 57 Gabon (%) | WER OpenSLR 57 Chad and Congo (%) | Planted errors kept (%) | Word timing | Word confidence | USD per audio hour |
|---|---|---|---|---|---|---|---|---|
| Whisper large-v3 (control, local CPU) | 8.2 | 11.8 | 7.7 | 4.7 | 82 | yes | yes | 0 (own compute) |
| Deepgram Nova-3 | not run | not run | not run | not run | not run | not run | not run | 0.26 list (0.29 streaming) |
| ElevenLabs Scribe v3 | not run | not run | not run | not run | not run | not run | not run | 0.20 list (0.22 live) |
| Speechmatics Enhanced | not run | not run | not run | not run | not run | not run | not run | 0.75 list (0.80 real time) |

- Sets: 60 Common Voice FR clips (CC0, test split, mirror `fsicoli/common_voice_22_0`), 83 OpenSLR 57 clips (Apache-2.0, from the `BrunoHays/small_african_accented_french_test` mirror of its test split, grouped by the country in the file name: all 47 Cameroon clips, 20 Gabon, 16 Chad and Congo), 22 planted-error sentences spoken by the Piper `fr_FR-siwis-medium` voice (CC BY 4.0). Clip lists are rebuilt from the seed; no audio or transcript is stored in the repository.
- Planted errors: the first run kept 15 of 22. Four of the seven losses were the test, not Whisper: errors that sound the same as the correct form (`visité` and `visitée`, `devenu` and `devenus`) or hide in an elision or liaison (`le adresse`, `une bon idée`). I replaced those four sentences with errors that change the sound (`je suis mangé`, `elles ont parti`, `le fenêtre`, `un nouveau maison`), re-synthesised and reran Whisper on the planted clips only: 18 of 22 kept (82%). The four still lost are the model: `un belle` and `elle est gentil` and `que tu viens` were rewritten to the standard form, and `un nouveau maison` was heard as `à nouveau maison`. Verdict: the test was part of the gap (15 to 18 once fixed), but Whisper still rewrites learner grammar, which is why it stays a control. The set was changed after looking at Whisper's output, so providers are scored on the revised set and the 15 of 22 stays on record.
- Latency is unmeasured. The local Whisper run took a median of 17 s a clip on a machine loaded with other jobs, which says nothing about a provider, so no latency number is reported. `python -m asr_benchmark stream` sends each clip at real-time pace over each provider's live endpoint and reports first-token and final latency (p50 and p95); it runs only when the key is set, and only on an idle machine.
- Cameroon (CA16) is 47 clips from a few speakers, so its rate is indicative only. The Yaoundé recordings (CTELL, 2003, 84 speakers, Apache-2.0, in the same OpenSLR 57 data) are now in the set as a fifth group: 60 clips from 34 speakers, read proverbs, taken from the first train shard of the `gigant/african_accented_french` mirror. Whisper scores 22.4% WER on them, far above the other groups, partly because the references fix spellings Whisper cannot hear (`a` and `à`, `ou` and `au`), so compare providers on it, not against the other groups. No other free public Cameroonian French set was found: a Hugging Face search returned only a 4.9 h commercial set (`africanspeech/cameroon-french-speech`) with no free licence. Not covered: LANGSNAP and FLLOC (access not requested), anglophone Cameroonians, streaming mode for the candidates.
- Free-allowance use, batch, full set of 225 clips = 14.0 min of audio (Common Voice 5.3, OpenSLR 57 Cameroon, Gabon, Chad and Congo 3.8, Yaoundé 4.1, planted 0.8). Deepgram: 14 min x $0.0043 = $0.06 of the $200 credit. ElevenLabs: 14 of 270 free batch minutes a month (5%). Speechmatics: 14 min x $0.75 an hour = $0.18 of the $100 credit. Every full run is far under the allowance, so no subset is needed. The harness keeps 30% of each allowance back (it stops an engine at 70%: 189 ElevenLabs minutes, $140 of Deepgram, $70 of Speechmatics), caches each transcript on disk by engine, model and clip so a rerun costs nothing, appends every call to a usage log, retries a transient failure twice at most, and stops an engine at the first 401, 402, 403 or 429. A streaming pass over 20 clips is about 2 more minutes per engine.
- Access failures, 2026-11-13, pilot of 12 clips: Deepgram answered 401 `INVALID_AUTH`, so the key in the dev config is not accepted by the API. ElevenLabs answered 401 `missing_permissions`: the key lacks the `speech_to_text` permission. Both engines stopped at the first call and no audio was billed. Speechmatics has no key yet.
- To finish: replace the Deepgram key, give the ElevenLabs key the speech-to-text permission, set `SPEECHMATICS_API_KEY`, rerun, then add the rows and the choice here.

## Consequences

- Good: a provider in milestone 0 without recruitment, consent forms or transcription costs; no personal data collected; the benchmark can be rerun on every provider or model change.
- Bad: the M0 choice rests mostly on read speech from adult Central African speakers and on British learners, not on our learners in exam conditions. Two engines close on the corpus may swap places on real learners.
- The launch criterion stays: before launch, the first 20 consenting beta learners record the speaking tasks and the benchmark reruns on their answers. The gate holds only if some of them are anglophone Cameroonians; if recruitment misses them, the launch criterion stays unmet and the volunteers fallback applies. If the winner then fails the 90% grading bar, the provider changes before launch.
- Design doc: sections 1, 8.5, 8.6, 18 and 19 and Appendices A and B changed in the same PR.

## Revisit when

- The first 20 consenting beta learners' recordings are in, before launch.
- A candidate provider changes its model or a new model is released for one of them.
- The top two engines finish within 1 WER point of each other.
