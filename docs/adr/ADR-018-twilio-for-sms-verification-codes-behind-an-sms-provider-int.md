# ADR-018: Twilio for SMS verification codes behind an SMS provider interface

- Status: Superseded by [ADR-023](ADR-023-email-verification-only-no-sms-sign-up.md) on 2026-11-05
- Date: 2026-10-22

## Context

The PRD allows sign-up with a phone number verified by code.

## Decision

Send verification codes through Twilio behind an SMS provider interface; register an alphanumeric sender ID with MTN in milestone 0, since provisioning can take up to 3 weeks.

## Alternatives considered

- **Local aggregators:** Kept as alternatives behind the same interface if delivery rates require it.

## Consequences

Low cost per message (about $0.0075 to Cameroon per a vendor comparison); delivery rates monitored.

## Sources

- https://sent.dm/resources/cameroon-sms-pricing
