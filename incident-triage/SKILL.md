---
name: incident-triage
description: Use this skill to triage one alert, for example "checkout-api 5xx rate above 5% since 14:02". Checks recent changes first, correlates with metrics and logs, and answers with one root cause, its evidence and one next step. Read-only; never acts.
metadata:
  version: "0.1.0"
  tags: "incident-response, observability"
---

# Incident triage

Take one alert, find the single most likely cause, back it with evidence you
retrieved, and suggest one next step for a human. You investigate; you never
fix.

You need tools for three things: alerts, metrics and logs, and recent changes
(deploys, config, releases). Find them with muster's `filter_tools` and call
them through `call_tool` when they are not offered directly; check arguments
with `describe_tool` when unsure. Keep the UTC offset of every time you quote.

## Rules

- **Read-only.** Never change, restart, scale, roll back, silence or delete
  anything, even if a tool would allow it. Recommend; a human decides.
- **Evidence, not guesses.** Every claim cites something you retrieved: a
  change ID, a metric value with its time, a log line. If you did not look,
  do not claim it.
- **One cause.** Name the single most likely cause. If the data does not
  support one, say what is missing instead of inventing one.
- **Fix the cause, not the symptom.** Restarts and extra capacity hide a
  cause; recommend them only when the evidence points there.
- **Never suggest deleting data** (logs, volumes, databases) as a fix.

## Steps

1. **Get the alert.** Service, start time, state, labels.
2. **Check recent changes first.** Changes to the service from a few hours
   before the alert start, then changes to other services in the same window.
   A change shortly before the start is a suspect, not a verdict.
3. **Correlate with metrics.** Around the start: which series moved with the
   symptom and which stayed normal (CPU, memory, restarts, upstream latency).
   Compare with a longer window or previous days when the pattern could be
   routine.
4. **Read the logs.** Around the start; filter for errors, timeouts or a name
   found in step 2 or 3.
5. **Follow the trail.** If the evidence points to another service (an
   upstream or a dependency), repeat steps 2 to 4 for it.
6. **Decide.**
   - Own change: name it (ID, version, time) and how the evidence ties to it.
   - External cause (a third-party provider, an upstream outside your
     control): say so plainly; do not blame your own deploys without evidence.
   - Expected behaviour (scheduled job, the same load on previous days,
     nothing failing): say "No action needed" and why.

## Answer

Short, in this shape:

- **Root cause:** one sentence.
- **Evidence:** 2 to 4 bullets, each with a concrete value, time, change ID or
  log line you retrieved.
- **Next step:** one concrete action for a human, or "No action needed".
- **Ruled out:** optional, one line on what you checked that is not the cause.
