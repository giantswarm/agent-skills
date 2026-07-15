---
name: sre
description: Use this skill for site reliability engineering work — investigating incidents, writing postmortems, authoring runbooks, managing alerts and silences, and troubleshooting Kubernetes workloads safely and methodically.
---

# Site Reliability Engineering

This skill provides vendor-neutral guidance for operating and troubleshooting
Kubernetes-based platforms with a Prometheus-style observability stack. It covers
the core SRE workflows: investigating incidents, running blameless postmortems,
authoring quality runbooks, managing alerts and silences, and triaging workloads
without making things worse.

The material is provider-agnostic. It assumes only that you have:

- One or more Kubernetes clusters (control-plane / workload split is common but not required).
- A metrics-and-logs stack (Prometheus/Mimir-style metrics, Loki/Elasticsearch-style logs,
  Grafana-style dashboards, an Alertmanager-style router).
- Alerting rules that page a human or on-call rotation.
- A GitOps or IaC workflow for changes.

## Core principles

Apply these throughout every workflow below.

1. **Non-invasive first.** Start read-only. Observe, gather, and correlate before
   you change anything. Never run a destructive or state-mutating action to
   "see what happens".
2. **Assess user impact early.** The first question in any incident is *who and
   what is affected, and how badly* — not *what is the root cause*. Impact drives
   urgency and communication.
3. **Correlate before acting.** Line up the timeline: when did symptoms start,
   what changed around then (deploys, config, scaling, upstream), and what else
   moved with it. Most incidents correlate to a recent change.
4. **Form a hypothesis, then verify it read-only.** State what you think is wrong
   and predict an observation that would confirm or refute it. Check that
   observation before you believe the hypothesis.
5. **Safety before speed.** Any mutating or risky action (restart, scale, delete,
   disable a policy, edit config) requires explicit confirmation and a stated
   expected effect and rollback. Never disable a security control to make a
   symptom disappear without owner approval.
6. **Blameless culture.** Incidents are caused by systems and conditions, not bad
   people. Write and speak about them that way — it is what makes honest
   postmortems and real fixes possible.
7. **Time-box your steps.** If a single investigative step runs long, stop,
   record what you have, and choose the next step deliberately rather than
   waiting indefinitely.

## When to use which reference

Load the reference that matches the task at hand:

- **[references/incident-response.md](references/incident-response.md)** — you are
  responding to a live alert or incident. A four-phase, read-only-first
  investigation protocol, severity guidance, communication cadence, and roles.
- **[references/postmortems.md](references/postmortems.md)** — the incident is
  resolved and you need to write it up. A blameless postmortem template and
  guidance on timelines, root cause, and action items.
- **[references/alerting-and-silences.md](references/alerting-and-silences.md)** —
  you are writing or reviewing alert rules, or you need to silence noisy alerts
  during maintenance or investigation. Covers alert-rule quality and the
  Alertmanager silence lifecycle.
- **[references/runbooks.md](references/runbooks.md)** — you are writing or
  reviewing an operational runbook. Structure, variable hygiene, review dates,
  ownership, and a quality checklist.
- **[references/observability.md](references/observability.md)** — you need to
  reason about signals, SLIs/SLOs and error budgets, or build/read dashboards.
- **[references/kubernetes-troubleshooting.md](references/kubernetes-troubleshooting.md)** —
  you are triaging a misbehaving Kubernetes workload. Non-invasive `kubectl`-first
  triage and a common-failure-modes table.
