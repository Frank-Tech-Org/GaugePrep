# ADR-023: Email verification only, no SMS sign-up

- Status: Accepted
- Date: 2026-11-05
- Supersedes: ADR-018

## Context

ADR-018 let learners sign up with a phone number verified by an SMS code sent through Twilio, with an MTN sender ID to register first. Every code costs money, the sender ID takes up to 3 weeks and an owner task, and a phone number is personal data we would otherwise not hold. The owner ruled on 2026-11-05 (D-13) that sign-up is verified by email only.

## Decision

Learners sign up with email and password, or with Google. The email address is verified by a single-use, time-limited code sent through Resend. No phone number is collected, and there is no SMS provider.

## Alternatives considered

- **Keep SMS through Twilio:** per-message cost, a sender ID registration and a phone number in `identity`; rejected by the owner.
- **SMS through a local aggregator:** same cost and data, a less known vendor.

## Consequences

- Good: no SMS spend, no sender ID wait, one less processor needing a data processing agreement, less personal data.
- Bad: a learner without a working email address must use Google or cannot sign up. If sign-up drop-off shows this matters, reopen it with the owner.
- The admin learner lookup searches by email only.
