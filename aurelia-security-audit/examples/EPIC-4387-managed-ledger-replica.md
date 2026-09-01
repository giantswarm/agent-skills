# EPIC-4387: Move the customer ledger read replica to a managed cloud database

**Team:** Core Banking
**Reporter:** A. Brummer
**Target:** Q4 2026

## Context

We run the customer ledger read replica on self-managed Postgres. It backs the
mobile app's balance and transaction history views, so it is on the critical
path for retail customers. Operating it costs the team roughly a day a week in
patching, failover drills and storage management, and we have had two
availability incidents this year traced to replica lag.

CloudScale DB (the provider's managed Postgres) would remove almost all of that
toil and gives us read scaling we currently do not have.

## Proposed approach

- Provision CloudScale DB in `eu-central-1` as the primary replica target.
- Add a standby in `us-east-1`. The provider only offers cross-region read
  replicas between these two regions on our current plan, and we want the DR
  option given this is on the retail critical path.
- Encryption at rest uses the provider's default managed keys. Their
  documentation states AES-256 and we see no reason to complicate the setup.
- Backups are handled by the provider: automated daily snapshots with 35-day
  retention and point-in-time recovery. This is better than what we do today,
  so we plan to decommission our own backup job for the replica.
- Cut over one read path at a time behind a feature flag, starting with
  transaction history.

## Out of scope

- The write primary stays where it is.
- Migrating other Postgres instances. If this goes well we will propose a
  broader move next quarter.

## Acceptance criteria

- Mobile balance and history views served from CloudScale DB
- Replica lag under 2 seconds at p99
- Team no longer spends time on replica patching
