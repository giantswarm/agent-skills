# EPIC-4401: Give the analytics group query access to the production data lake

**Team:** Data Platform
**Reporter:** R. Feldkamp
**Target:** Q4 2026

## Context

The analytics group builds the retail behaviour models. Today they work from a
nightly extract that lands in their own bucket, which means their features are
always a day stale and every new field they want is a two-week request cycle to
us. They have asked repeatedly for direct query access and the model refresh
cadence is now a stated OKR for the retail business.

We looked at this last year and it did not go ahead, but the tooling has moved
on since and we think the controls are now good enough.

## Proposed approach

- Create an `analytics-readonly` role in the lakehouse with SELECT on the
  `retail_*` schemas.
- Apply row-level security so analysts only see rows for customers who have
  consented to analytics processing.
- Apply column-level grants so the role cannot select `national_id`,
  `full_account_number` or `date_of_birth`.
- Grant the role to the eight named analysts in the group. Access is persistent
  rather than request-based, because their work is continuous and JIT approval
  for every query session would defeat the point.
- Leave the nightly extract running for six months as a fallback, then retire it.

## Out of scope

- Write access. Analysts do not need it.
- The fraud team's access, which is separate and already approved.

## Acceptance criteria

- Named analysts can query `retail_*` directly with under 1 hour data latency
- Restricted columns are not selectable through the role
- The nightly extract pipeline can be retired after the transition period
