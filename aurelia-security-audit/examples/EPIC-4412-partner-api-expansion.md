# EPIC-4412: Open the Payments API to three additional partner banks

**Team:** Payments Platform
**Reporter:** J. Vandermeer
**Target:** Q4 2026

## Context

The partner-bank pilot has been running since October with Bank Solera and
Cortez Financial. Both are happy and commercial has signed three more partners
(Northmoor, Banca Lentini, Kestrel Direct) who want to be live before year end.
The pilot integration works, so this is mostly a matter of onboarding three more
consumers onto the same path.

Partner volume is currently around 40k requests/day combined. With five
partners we expect roughly 150k/day.

## Proposed approach

- Reuse the dedicated partner ingress that the pilot terminates TLS on. It
  already handles the client-certificate scheme the partners' middleware needs,
  and the managed gateway still does not support it.
- Issue each partner an API key, delivered over our support portal. The key is
  read by the partner-api service from `PARTNER_API_KEYS` in the deployment
  environment, as a comma-separated list. Adding a partner is a values change.
- Add the three partners to the existing `partner-api` namespace. No new
  namespaces or network policy changes needed since the ingress path is
  unchanged.
- Enable full request and response logging on the partner-api service for the
  first six weeks of each onboarding. Partner integration bugs have been very
  hard to debug from our side and having the payloads has saved us days.
- Expose `/v2/accounts/{id}/instruments`, which the new partners need and the
  pilot partners did not use. It returns the customer's stored payment
  instruments including the masked card number and the full expiry date.

## Out of scope

- Managed gateway migration. Tracked separately, no date yet.
- Rate limiting. The pilot has not needed it and partners are contractually
  capped.

## Acceptance criteria

- Three new partners can authenticate and call the v2 endpoints
- Onboarding a further partner is a values change, no code deploy
- Integration issues can be diagnosed from our logs without partner involvement
