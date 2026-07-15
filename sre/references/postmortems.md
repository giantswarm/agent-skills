# Postmortems

A postmortem is the written record of an incident: what happened, why, and what
will change so it does not happen the same way again. Postmortems are
**blameless** — they explain outcomes through systems and conditions, never
through individual fault. That is what makes people comfortable being honest,
which is what makes the analysis useful.

## When to write one

Write a postmortem for any incident that caused user-visible impact, required
coordinated response, or surprised you. Near-misses that could easily have been
serious are worth writing up too. Trivial, well-understood, single-step issues
usually are not.

## Principles

- **Blameless.** Describe what the system allowed to happen. Replace "X made a
  mistake" with "the system permitted an unsafe action without a guardrail".
- **Factual and timestamped.** Build the narrative from evidence and a timeline,
  not memory or impression.
- **Action-oriented.** The payoff is concrete, owned, tracked follow-up work —
  not just a story.
- **Honest about the unknown.** If root cause is unconfirmed, say so and note
  what would confirm it.
- **Safe to publish.** Keep credentials, personal data, and customer identifiers
  out. Write as if it may be read widely.

## Template

```markdown
# Postmortem: <short incident title>

## Summary
2–3 sentences: what happened, the impact, and how it was resolved.

## Impact
- Severity:
- Duration: <detection → resolution>, plus time-to-detect and time-to-mitigate
- Who/what was affected and how severely
- Quantified where possible (error rate, requests failed, users affected)

## Timeline
All times in a single timezone (UTC recommended).
- T0  root-cause change or trigger
- T1  first symptom
- T2  detection (how was it noticed?)
- ...  key investigation steps and actions
- Tn  mitigation
- Tn+  full resolution

## Root cause
The technical chain of causation. What actually broke and why.

## Contributing factors
Conditions that made the incident possible, worse, or slower to detect/resolve
(e.g. missing alert, unclear runbook, insufficient capacity headroom, a fragile
dependency). These often matter more than the single "root cause".

## What went well
Detection, tooling, or response steps worth keeping and reinforcing.

## What went poorly / where we got lucky
Gaps, and places a slightly different situation would have been much worse.

## Action items
| Action | Type (detect / prevent / mitigate) | Owner | Tracking link |
|--------|-----------------------------------|-------|---------------|
| ...    | ...                               | ...   | ...           |

## References
Dashboards, alerts, related changes, discussion threads (links only; no secrets).
```

## Writing good action items

- Each action item is **specific, owned, and tracked** as a real work item —
  not a vague aspiration.
- Prefer systemic fixes over "be more careful". Add a guardrail, an alert, a
  test, a limit, or automation.
- Balance the three types: **prevent** the cause, **detect** it faster next time,
  and **mitigate** faster when it recurs.
- Do not over-generate. A handful of high-value, actually-completed items beats a
  long list that rots.

## Timeline tips

- Anchor to the trigger (a change, a spike, an upstream event), not to when you
  woke up.
- Capture **time-to-detect** and **time-to-mitigate** explicitly — they are the
  numbers you most want to drive down.
- Note every mutating action during response, so the timeline explains recovery.
