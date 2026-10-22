# ADR-006: Chained voice pipeline on LiveKit Agents instead of a speech-to-speech model

- Status: Accepted
- Date: 2026-10-22

## Context

The speaking examiner must reply in under 2.5 s, follow strict task rules, understand Cameroonian accents, and produce a word-level transcript of the learner's own words for grading.

## Decision

Use LiveKit Agents (Python) with the LiveKit media server, the LiveKit turn detector (French supported), and a chain of streaming speech recognition, Claude Haiku 5.5 for the examiner's lines, and ElevenLabs Flash for the voice. Record the learner on the server and transcribe in batch for grading.

## Alternatives considered

- **Speech-to-speech models (gpt-realtime-2.1, gemini-3.8-live):** Rejected: recognition locked to the vendor; examiner rules harder to enforce; OpenAI deprecated its previous realtime models within the year and Google states no minimum notice.
- **Pipecat:** Rejected: its free transport is advised against beyond a handful of concurrent sessions; production needs a third-party transport anyway.

## Consequences

Each stage is replaceable; the chain adds roughly 300 to 800 ms, inside the latency budget. A media server must be run (free tier in staging, self-hosted in production).

## Sources

- https://www.forasoft.com/blog/article/pipecat-vs-livekit-agents
- https://docs.pipecat.ai/client/concepts/choosing-a-transport
- https://docs.livekit.io/agents/logic/turns/turn-detector.md
- https://developers.openai.com/api/docs/deprecations
- https://ai.google.dev/gemini-api/docs/deprecations?hl=en
