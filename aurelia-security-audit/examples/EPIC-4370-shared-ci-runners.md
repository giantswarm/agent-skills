# EPIC-4370: Consolidate CI onto a shared runner pool for all teams

**Team:** Developer Experience
**Reporter:** K. Osei
**Target:** Q4 2026

## Context

We currently run 14 separate runner pools, one per team. Utilisation across them
averages 11%, so we are paying for roughly nine times the compute we need, and
every pool needs its own maintenance. Finance has asked us twice to bring the CI
bill down.

A single autoscaling pool would cut the spend substantially and give teams faster
queue times at peak, since they would draw from shared capacity instead of
waiting on their own eight runners.

## Proposed approach

- Stand up one autoscaling runner pool sized for aggregate peak.
- Migrate teams onto it in waves, two teams a week.
- Runners are ephemeral: each job gets a fresh container from a clean image.
- Team credentials continue to be injected from the secret manager at job start,
  as they are today.
- Decommission the per-team pools as each team migrates.

We know isolation has come up before. Ephemeral containers per job address it:
because every job starts from a clean image there is no persistence between jobs,
so credentials from one team's job cannot be visible to another's. We will
implement per-job credential scoping as a follow-up once the migration is done,
to tighten it further.

## Out of scope

- Self-hosted runners for the two teams with hardware-token signing needs.
- Changing the build images themselves.

## Acceptance criteria

- All 12 eligible teams on the shared pool
- CI compute spend down at least 60%
- p50 queue time no worse than today
