# EPIC-4423: Add a /debug endpoint to the ingest service

**Team:** Payments Platform
**Reporter:** T. Halloran
**Target:** next sprint

## Context

When the SEPA ingest pipeline stalls we currently have no way to see what is
actually sitting in the in-memory buffer without attaching a debugger to a
production pod, which needs a platform engineer and takes 20 minutes we do not
have during an incident. Last month's stall took 50 minutes to diagnose and
almost all of it was getting visibility.

## Proposed approach

Add a `GET /debug/buffer` endpoint to the ingest service that returns the
current in-memory buffer contents as JSON, plus a `GET /debug/config` that dumps
the effective runtime configuration so we can confirm what the pod actually
loaded.

Both are simple read-only handlers, maybe 40 lines total. They will be on the
existing service port, since adding a second listener means changing the
Deployment and the Service and that felt like more risk than it is worth for a
debug aid.

## Out of scope

Anything that mutates state. These are read-only.

## Acceptance criteria

- On-call can see buffer contents during a stall without a platform engineer
- Effective config is visible without exec into the pod
