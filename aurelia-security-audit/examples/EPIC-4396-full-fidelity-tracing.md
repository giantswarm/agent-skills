# EPIC-4396: Enable full-fidelity tracing on the payments path

**Team:** Observability
**Reporter:** M. Sandoval
**Target:** Q4 2026

## Context

We sample traces at 1% on the payments path. That is fine for latency
percentiles but useless for debugging a specific failed payment, which is what
support and the payments team actually ask us for. Every escalation currently
turns into "we do not have the trace for that transaction".

The tracing backend has capacity headroom after the storage tier upgrade in
July, so we can afford far more volume than we currently send.

## Proposed approach

- Raise sampling to 100% on the payments path. Other paths stay at 1%.
- Enable payload capture on the OpenTelemetry HTTP and gRPC instrumentation, so
  spans carry the request and response bodies. This is the part support actually
  needs: knowing a call failed is not enough, they need to see what was sent.
- Keep the existing 30-day retention on trace data. No change to the storage
  configuration is needed.
- Add a support-facing lookup so an agent can paste a payment reference and get
  the trace.

## Out of scope

- Changing retention. Covered by the existing arrangement with the security team.
- Log volume. This is traces only.

## Acceptance criteria

- Any payment in the last 30 days can be retrieved as a full trace
- Support can self-serve trace lookup by payment reference
- No increase in payments-path p99 latency beyond 2ms
