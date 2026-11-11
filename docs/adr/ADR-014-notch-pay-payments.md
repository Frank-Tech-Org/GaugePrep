# ADR-014: Notch Pay for payments; automatic card renewal after release 1

- Status: Accepted
- Date: 2026-10-22

## Context

Release 1 targets Cameroon, where MTN Mobile Money and Orange Money dominate. Stripe is not available to Cameroonian businesses. Notch Pay documents mobile money, wallets, USSD and QR payments but no recurring card payments.

## Decision

Integrate Notch Pay behind a payment provider interface: our reference on every payment, access granted only after a signature-verified webhook and a status check, reconciliation every 15 minutes, raw webhooks stored. Renewals use reminders and one-step payment. Automatic card renewal ships with the release that opens markets outside CEMAC (PRD PAY-3 updated).

## Alternatives considered

- **Merchant-of-record platforms:** Deferred: availability for Cameroonian sellers not established.

## Consequences

Card availability and test setup are confirmed with Notch Pay in milestone 0.

## Sources

- https://developer.notchpay.co/accept-payments/charge
- https://developer.notchpay.co/accept-payments/mobile-money.md
- https://developer.notchpay.co/accept-payments/other-methods
