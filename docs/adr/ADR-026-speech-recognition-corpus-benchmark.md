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
- Engines and free allowances, checked 2026-11-12: Deepgram Nova-3 Multilingual, $200 credit for new accounts, $0.0092 a minute streaming and $0.0052 batch at list price (https://deepgram.com/pricing). ElevenLabs Scribe v3 at $0.20 an hour and Scribe v3 Live at $0.22, with 4 h 30 min batch and 2 h 30 min live a month free (https://elevenlabs.io/pricing/api). Mistral Voxtral Mini 4B Realtime, open weights under Apache-2.0 (https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602).

## Decision

The provider is chosen by a benchmark on public corpora, run once in milestone 0:

- Accented French: OpenSLR 57, with Cameroonian speakers kept as their own group in the results.
- Learner French from English speakers: LANGSNAP and FLLOC, for internal measurement only. Their audio and transcripts never enter the repository, a model, a prompt or the product, and only aggregate numbers are published. If TalkBank or Oxford refuse a company's evaluation use, that set is dropped and the claim below narrows to Central African French.
- Control: Common Voice French scripted and spontaneous speech.
- Error preservation: scripted learner sentences with planted grammatical errors, spoken by a synthetic voice. This set measures preservation only, never accent accuracy.
- Candidates, each streaming and batch: Deepgram Nova-3 Multilingual, ElevenLabs Scribe v3 Live and Scribe v3, Mistral Voxtral Realtime. Whisper large-v3 runs as a control and cannot win.
- A fixed, seeded subset sized to stay inside each provider's free allowance; any paid spend goes to the owner first.
- One text normaliser for every engine; results by corpus and speaker code only.

ADR-008's rule picks the winner, unchanged: the lowest word error rate among candidates that preserve at least 95% of the learner's errors and return word-level timing and confidence; within one point of word error rate, the cheaper wins. Latency and price per audio hour are measured and reported.

Public wording is "tested on Central African and English-speaking learner French". We make no claim for anglophone Cameroonians, spontaneous A2 to C1 speech, or phone microphones on slow networks.

## Results

Run 2026-11-13 with `tooling/asr_benchmark` (seed 15, batch mode, one normaliser for every engine). Only Whisper large-v3 has run: the other three engines are skipped until their API keys exist, so no provider is chosen yet.

| Engine | WER Common Voice FR (%) | WER OpenSLR 57 Cameroon (%) | WER OpenSLR 57 Gabon (%) | WER OpenSLR 57 Chad and Congo (%) | Planted errors kept (%) | Word timing | Word confidence | USD per audio hour |
|---|---|---|---|---|---|---|---|---|
| Whisper large-v3 (control, local CPU) | 8.2 | 11.8 | 7.7 | 4.7 | 68 | yes | yes | 0 (own compute) |
| Deepgram Nova-3 | not run | not run | not run | not run | not run | not run | not run | 0.31 list |
| ElevenLabs Scribe v3 | not run | not run | not run | not run | not run | not run | not run | 0.20 list |
| Mistral Voxtral | not run | not run | not run | not run | not run | not run | not run | not checked |

- Sets: 60 Common Voice FR clips (CC0, test split, mirror `fsicoli/common_voice_22_0`), 83 OpenSLR 57 clips (Apache-2.0, from the `BrunoHays/small_african_accented_french_test` mirror of its test split, grouped by the country in the file name: all 47 Cameroon clips, 20 Gabon, 16 Chad and Congo), 22 planted-error sentences spoken by the Piper `fr_FR-siwis-medium` voice (CC BY 4.0). Clip lists are rebuilt from the seed; no audio or transcript is stored in the repository.
- Whisper kept 15 of 22 planted errors; the other seven were corrected in the transcript, which is the failure ADR-008 warns about. Streaming latency is not measured: the script runs batch only, and the local CPU time (median 17 s a clip, on a shared, loaded machine) says nothing about the providers.
- Cameroon is 47 clips from the CA16 recordings, a few speakers, so its rate is indicative only. Not covered yet: the Yaoundé recordings (end of the 1.8 GB archive), LANGSNAP and FLLOC (access not requested), streaming mode for the candidates.
- To finish: set `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY` and `MISTRAL_API_KEY`, rerun, then add the rows and the choice here.

## Consequences

- Good: a provider in milestone 0 without recruitment, consent forms or transcription costs; no personal data collected; the benchmark can be rerun on every provider or model change.
- Bad: the M0 choice rests mostly on read speech from adult Central African speakers and on British learners, not on our learners in exam conditions. Two engines close on the corpus may swap places on real learners.
- The launch criterion stays: before launch, the first 20 consenting beta learners record the speaking tasks and the benchmark reruns on their answers. The gate holds only if some of them are anglophone Cameroonians; if recruitment misses them, the launch criterion stays unmet and the volunteers fallback applies. If the winner then fails the 90% grading bar, the provider changes before launch.
- Design doc: sections 1, 8.5, 8.6, 18 and 19 and Appendices A and B changed in the same PR.

## Revisit when

- The first 20 consenting beta learners' recordings are in, before launch.
- A candidate provider changes its model or a new model is released for one of them.
- The top two engines finish within 1 WER point of each other.
