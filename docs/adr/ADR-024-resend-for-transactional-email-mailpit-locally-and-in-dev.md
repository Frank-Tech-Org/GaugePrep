# ADR-024: Resend for transactional email, Mailpit locally and in dev

- Status: Accepted (technical shape under D-11; the accounts and DNS are owner actions)
- Date: 2026-11-05

## Context

Sign-up is verified by an emailed code only (ADR-023), so email is on the critical path of the first journey. The architecture named Resend for dev, staging and production and listed it as a processor, but no ADR recorded why or checked its free plan. Rule D-7: free or self-hosted in dev and staging, paid only in production. Dev and staging hold synthetic data only. Facts checked on 2026-11-05:

| | Resend free | Brevo free | Amazon SES |
|---|---|---|---|
| Volume | 3,000 a month, 100 a day | 300 a day, about 9,000 a month | Sandbox sends only to verified addresses; production access needs an AWS review |
| Custom domain | Yes, 3 domains | Yes | Yes |
| Branding | None | Brevo logo on free-plan mail | None |
| Data location | Account data, logs and message content stored in the US; sending region selectable (EU Ireland available) | Hosted in France and Germany; some US sub-processors | Region chosen (eu-central-1 Frankfurt) |
| DPA | Article 28 DPA binds every account on accepting the terms; SCCs plus EU-US Data Privacy Framework | DPA is an appendix to the terms; SCCs and DPF for US sub-processors | AWS GDPR DPA in the service terms |
| SMTP | `smtp.resend.com`, port 587 STARTTLS, user `resend`, API key as password | Yes | Yes |
| Next tier | Pro $20 a month for 50,000, no daily cap | Starter $9 a month, no daily cap | $0.10 per 1,000 |
| Acceptable use | Opt-in mail only; bounces under 4%, complaints under 0.08% | Similar | Similar, account review |

## Decision

- The backend sends through Django's built-in SMTP email backend, configured by environment keys only. No provider SDK enters the lockfile, so the provider changes by config, not code.
- Local and dev send to Mailpit (MIT, v1.33.0 of 31 October 2026, Docker image, no lockfile entry). Dev seeds synthetic addresses, and real sends to them would bounce and push the Resend account past its 4% bounce limit. Use v1.32.0 or later: GHSA-379p-g4f4-hq5h (High) is fixed there. Mailpit's web UI is never exposed publicly in dev; reach it through an SSH tunnel.
- Staging and production send through Resend on the free plan, from the EU (Ireland) sending region, on a subdomain of gaugeprep.com with SPF, DKIM and DMARC. Each gets its own API key with sending access only.
- Moving production to Resend Pro ($20 a month) when it reaches 100 emails a day is an owner decision about money.

## Alternatives considered

- **Brevo free:** 3 times the daily volume and EU hosting, but a logo on free mail, transactional and marketing share the 300 cap, and reviews report weaker transactional deliverability. Best fallback if the owner wants EU-stored mail logs; switching is a config change.
- **Amazon SES:** cheapest at volume and region-pinned to Frankfurt, but the sandbox only reaches verified addresses and leaving it needs an AWS account review, so staging cannot send to a demo tester without that step.
- **The owner's domain mailbox over SMTP:** free, but mailbox providers throttle and flag automated sending, and there are no bounce or complaint reports.
- **Resend in dev as well (the previous plan):** spends the 100-a-day cap on ticket QA and bounces on synthetic addresses.

## Consequences

- Good: no new code dependency; dev costs nothing and can't hurt sender reputation; one config change swaps provider.
- Bad: learner email addresses and code emails sit in Resend's US storage for 30 days under SCCs and the DPF, while the rest of our data is in the EU; the privacy notice must name this transfer. 100 a day caps staging and early production.
- Owner actions: create the Resend account (in a GaugePrep name, not a personal one), add the sending subdomain and its DNS records in Cloudflare, and paste the API keys as values.
- Reopen if sign-ups exceed 100 a day, if the DPF is struck down, or if Resend changes its free plan.
