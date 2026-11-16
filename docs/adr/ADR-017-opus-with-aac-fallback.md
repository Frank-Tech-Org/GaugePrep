# ADR-017: Opus with AAC fallback for audio

- Status: Accepted
- Date: 2026-10-22

## Context

Listening audio must be small for 3G and playable on all target phones.

## Decision

Encode listening audio once as Opus 24 kb/s mono (recommended for spoken word) and AAC as a fallback for iOS before 18.4; serve content-hashed files from the edge. Record speaking on the server as Opus.

## Alternatives considered

- **MP3 only:** Rejected: larger files for the same speech quality.

## Consequences

Two files per item in storage; the PWA picks the playable one.

## Sources

- https://wiki.xiph.org/Opus_Recommended_Settings
- https://caniuse.com/opus
