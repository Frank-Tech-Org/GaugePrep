# ADR-008: Speech recognition chosen by a measured accent test

- Status: Superseded by [ADR-026](ADR-026-speech-recognition-corpus-benchmark.md) on 2026-11-12
- Date: 2026-10-22
- Replaced by: [ADR-026](ADR-026-speech-recognition-corpus-benchmark.md), speech recognition chosen by a public-corpus benchmark

## Context

No vendor publishes accuracy for Cameroonian French; Microsoft lists only European and Canadian French locales. Grading needs learner errors preserved in transcripts.

## Decision

Run a test in milestone 0 with 20 consenting Cameroonian speakers (francophone and anglophone, A2 to C1) on the three TCF speaking tasks, against verbatim human transcripts. Candidates: Deepgram Nova-3 Multilingual, Mistral Voxtral Realtime, ElevenLabs Scribe v2 Realtime. Choose the lowest word error rate among candidates that preserve at least 95% of learner errors and provide word timing and confidence; within one point, the cheaper wins.

## Alternatives considered

- **Pick by public leaderboard:** Rejected: leaderboards do not cover Cameroonian French or error preservation.

## Consequences

The winner serves both live and batch transcription; the test is repeated whenever the provider or model changes.

## Sources

- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
- https://deepgram.com/pricing
- https://aibusiness.com/generative-ai/mistral-drops-new-speech-to-text-ai-models
- https://elevenlabs.io/pricing/api
