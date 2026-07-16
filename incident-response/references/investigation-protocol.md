# Investigation protocol

A structured, read-only-first protocol for investigating a live incident on a
Kubernetes-based platform. The goal is to understand and mitigate impact
quickly without introducing new failures.

## Roles

Even a small response benefits from separating concerns:

- **Investigator / operator** — drives the technical investigation and any
  remediation. Focuses on the system.
- **Incident coordinator** — owns communication, keeps the timeline, pulls in
  extra help, and shields the investigator from status-update churn.
- **Communications** — keeps affected users and stakeholders informed. In small
  incidents the coordinator does this too.

For a minor issue one person may hold all roles. For anything customer-facing or
prolonged, split them.

## Severity

Classify early; re-classify as you learn more. A simple, effective scale:

| Severity | Meaning | Examples |
|---|---|---|
| SEV1 / critical | Widespread outage or data loss; core function unavailable | Control plane down, cluster-wide networking broken, data corruption |
| SEV2 / major | Significant degradation; a major feature or a subset of users impaired | One workload cluster degraded, elevated error rate, key service slow |
| SEV3 / minor | Limited or cosmetic impact; no user-facing outage | Single non-critical pod crash-looping, noisy alert, redundant capacity lost |

Severity drives urgency, who gets paged, and how often you communicate.

## The four-phase protocol

### Phase 0 — Triage the alert itself

Before diving in, read the alert. What condition fired, on what object, since
when, and does a runbook link exist? If a documented triage procedure or runbook
exists for this alert, follow it first — it usually encodes hard-won knowledge.

### Phase 1 — Assess impact and scope (read-only)

- What is broken from the user's perspective? What is *not* broken?
- Which clusters, namespaces, services, or tenants are affected?
- When did symptoms start? Is it ongoing, intermittent, or resolved?
- Is it getting worse, stable, or recovering?

Set/confirm severity from the answers. This phase decides urgency.

### Phase 2 — Collect data (read-only)

Gather signals in parallel; do not mutate anything.

- **Alerts & pages** — what fired, in what order, and what cleared.
- **Kubernetes state** — object status, events, conditions, restart counts,
  recent rollouts (`kubectl get/describe/logs`, events sorted by time).
- **Metrics** — error rate, latency, saturation (CPU/memory/disk), request
  volume, for the affected components and their dependencies.
- **Logs** — errors and warnings around the start time; correlate with deploys.
- **Change history** — recent deploys, config changes, scaling events, GitOps
  syncs, certificate/secret rotations, upstream provider events.
- **Network & policy** — connectivity, DNS, ingress, network policy, TLS.

Build a timeline as you go. The single most useful artifact is *"symptom X
started at T; change Y landed at T-ε"*.

### Phase 3 — Hypothesize and verify (read-only)

- State a specific hypothesis: *"Service A is failing because dependency B
  started returning 5xx after its config change at T."*
- Predict an observation that would confirm or refute it, then check it.
- Prefer the hypothesis with the most supporting evidence and the fewest
  assumptions. Discard refuted hypotheses explicitly.
- Only after a hypothesis holds do you consider a mutating action — and then only
  with a stated expected effect and rollback, and confirmation appropriate to the
  blast radius.

### Phase 4 — Mitigate, then report

- **Mitigate before you fully fix.** Restoring service (failover, rollback,
  scale-out, traffic shift) usually outranks understanding the last detail.
  Reversible mitigations are preferred.
- Record what you did, when, and its effect on the timeline.
- Produce a structured handoff/report (below). If the incident is resolved,
  hand off to the postmortem process.

## Report format

```
## Summary
One or two sentences: what happened, impact, current status.

## Timeline
- T0  first symptom / trigger
- T1  detection (alert fired / reported)
- ...  key observations and actions, each timestamped
- Tn  mitigation / resolution

## Impact
Who and what was affected, for how long, and how severely.

## Findings
What the evidence shows. Distinguish confirmed facts from hypotheses.

## Suspected root cause
Best current explanation. Say "unconfirmed" if it is.

## Actions taken
Mitigations and changes made during the incident, with effects.

## Recommended follow-ups
Short-term hardening and longer-term fixes (feeds the postmortem action items).
```

## Safety rules

- Default to read-only. Investigation must never make the incident worse.
- Never take a destructive or irreversible action without explicit confirmation
  and a rollback plan.
- Never disable a security control (policy, network policy, admission control,
  authentication) to clear a symptom without owner approval.
- Do not force-push, amend shared history, or bypass GitOps to make an urgent
  change — go through the normal change path unless a break-glass procedure
  explicitly applies.
- Keep sensitive data (credentials, tokens, personal data, customer identifiers)
  out of tickets, chat, and reports.
