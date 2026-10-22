# ADR-009: ElevenLabs for examiner and content voices

- Status: Accepted
- Date: 2026-10-22

## Context

The examiner needs low-latency French speech; listening content needs varied voices and African francophone accents, which no vendor offers as a locale.

## Decision

Use ElevenLabs Flash ($0.04 per 1,000 characters) for the examiner and v3 ($0.08) for listening content, and create African francophone voices from recordings of consenting local speakers. Content audio is generated once and reused.

## Alternatives considered

- **Provider voices only:** Rejected: no Cameroonian or West African French locale available.

## Consequences

Voicing the full launch bank costs roughly $25 to $50. Consent records are kept for every cloned voice.

## Sources

- https://elevenlabs.io/pricing/api
