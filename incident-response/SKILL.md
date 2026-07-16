---
name: incident-response
description: Use this skill to investigate and respond to live incidents on Kubernetes-based platforms — assessing user impact, gathering and correlating signals, forming and verifying hypotheses read-only, and mitigating safely without making things worse.
---

# Incident response

This skill guides the investigation and response to a live incident on a
Kubernetes-based platform with a Prometheus-style observability stack. The goal
is to understand and mitigate impact quickly, without introducing new failures.

It assumes only that you have one or more Kubernetes clusters, a
metrics-and-logs stack (Prometheus/Mimir-style metrics, Loki/Elasticsearch-style
logs, Grafana-style dashboards, an Alertmanager-style router), and alerting that
pages a human. It is provider-agnostic.

## Core principles

Apply these throughout the response.

1. **Non-invasive first.** Start read-only. Observe, gather, and correlate before
   you change anything. Never run a destructive or state-mutating action to
   "see what happens".
2. **Assess user impact early.** The first question is *who and what is affected,
   and how badly* — not *what is the root cause*. Impact drives urgency and
   communication.
3. **Correlate before acting.** Line up the timeline: when symptoms started, what
   changed around then (deploys, config, scaling, upstream), and what moved with
   it. Most incidents correlate to a recent change.
4. **Form a hypothesis, then verify it read-only.** State what you think is wrong
   and predict an observation that would confirm or refute it. Check that
   observation before you believe the hypothesis.
5. **Safety before speed.** Any mutating or risky action (restart, scale, delete,
   disable a policy, edit config) requires explicit confirmation and a stated
   expected effect and rollback. Never disable a security control to make a
   symptom disappear without owner approval.
6. **Time-box your steps.** If a step runs long, stop, record what you have, and
   choose the next step deliberately rather than waiting indefinitely.

## Workflow at a glance

1. **Triage the alert** — read what fired, on what, since when; follow the alert's
   runbook if one exists.
2. **Assess impact and scope** (read-only) — what is broken for users, where, since
   when, and getting worse or recovering. Set severity.
3. **Collect data** (read-only) — alerts, Kubernetes state, metrics, logs, change
   history, network/policy. Build a timeline.
4. **Hypothesize and verify** (read-only) — one specific hypothesis at a time,
   confirmed by a predicted observation.
5. **Mitigate, then report** — restore service with a reversible mitigation where
   possible; record actions; hand off to the postmortem process.

## References

- **[references/investigation-protocol.md](references/investigation-protocol.md)** —
  the full four-phase protocol: roles, severity scale, per-phase steps, the
  structured report format, and the hard safety rules. Start here during a live
  incident.
- **[references/observability.md](references/observability.md)** — which signals to
  gather and how to correlate metrics → logs → traces; golden signals and
  SLO burn-rate thinking.
- **[references/kubernetes-troubleshooting.md](references/kubernetes-troubleshooting.md)** —
  non-invasive, `kubectl`-first triage sequence and a common-failure-modes table
  for misbehaving workloads.

When the incident is resolved and needs writing up, use the **`postmortems`**
skill.
