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

## Sandbox confirmation (2026-11-13)

- **Mobile money:** sandbox payments on `cm.mtn` and `cm.orange` ended `complete` with the success test numbers (`+237670000000`, `+237690000000`) and `failed` with the failure ones (`+237670000002`, `+237690000002`). Flow: `POST /payments` (public key in `Authorization`), `POST /payments/{reference}` with `channel` and `data.phone`, then poll `GET /payments/{reference}`.
- **Webhook signature:** `x-notch-signature` is the hex HMAC SHA-256 of the raw request body, keyed with the webhook hash (`NOTCHPAY_WEBHOOK_HASH`, separate from the API keys; sandbox and live hashes differ). Compare in constant time. The vendor's JavaScript example signs `JSON.stringify(req.body)`, which can differ from the bytes sent; we sign the stored raw body. Source: https://developer.notchpay.co/get-started/webhooks/verify.md. Not yet checked against a real delivery; the payment module's first test does that.
- **Replays and forgeries:** a unique constraint on the provider reference absorbs replayed deliveries, access is granted only after `GET /payments/{reference}` returns `complete`, and a missing or non-hex signature is rejected before the comparison.
- **Cards:** the channels list returns a `card` channel for all countries, XAF, 1,000 to 5,000,000, but `active: false` and `live: false` on our account. The public docs describe no card flow and no recurring or tokenised charges. Card availability and renewal are open questions for Notch Pay support.
