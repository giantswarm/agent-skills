# EPIC-4431: Migrate to the new internal CA with 30-day certificate lifetimes

**Team:** Platform Security
**Reporter:** L. Achterberg
**Target:** Q4 2026

## Context

The current internal CA issues 12-month certificates and renewal is a manual
ticket. We have had two outages in 18 months from expired internal certificates,
and the long lifetime means a compromised key stays useful for a year.

The new CA supports ACME, so workloads can renew automatically. We want to move
the estate to 30-day certificates with automated renewal at 20 days.

## Proposed approach

- Stand up the new CA alongside the existing one. Both trusted during migration.
- Add the new CA to the platform trust bundle, rolled out cluster by cluster.
- Migrate workloads in waves by namespace, starting with non-production, then
  production non-critical, then the payments path.
- Automated renewal via cert-manager for anything running on the platform.
- Retire the old CA once no certificates it issued remain in use.

## Known complications

- The legacy settlement adapter cannot use ACME. It runs on the mainframe side
  and its certificate is installed by hand. We plan to leave it on the old CA
  for now and handle it when the adapter is decommissioned.
- A handful of partner-facing certificates are pinned by partners. Shortening
  those lifetimes needs partner coordination, so they stay at 12 months until
  each partner confirms.

## Out of scope

- External, publicly trusted certificates. Different CA, different process.

## Acceptance criteria

- All platform workloads on 30-day certificates with automated renewal
- No manual certificate renewal tickets for platform workloads
- Old CA retired or scoped to the documented exceptions
