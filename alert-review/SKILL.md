---
name: alert-review
description: Use this skill to run a periodic (weekly) alert review — "review last week's alerts", "alert review", "what paged us and why" — over PagerDuty incidents, the Slack discussions around them, and monitoring evidence. Produces recurring-alert trends, human cost per incident, noisy/silenceable candidates, and evidence-backed action items.
metadata:
  version: "0.1.0"
---

# Alert review

Review a window of alerts (default: the last 7 days) and report what paged
humans, what it cost, and what to change. Every claim in the output carries its
evidence: an incident id, a Slack permalink-equivalent (channel + ts), a metric,
or a log line.

All tools run through muster's `call_tool` with their full catalogue names:
`x_pagerduty_*`, `x_slack_*`, `x_workload-monitoring_*`. Time parameters
accept ISO-8601 or relative offsets like `-7d`.

Write actions (acknowledging/resolving incidents, posting to Slack, creating
silences) may be in your toolset; the review itself stays read-only — use a
write only when the user explicitly asks for one.

## Workflow

1. **Window.** Default `since: -7d`. Use the window the user names; say which
   window you used.

2. **Pull incidents.** `x_pagerduty_list_incidents {since, until?}` — no
   urgency/status filter; the review needs the noise too. For anything
   non-trivial, `x_pagerduty_get_incident` and
   `x_pagerduty_list_alerts_for_incident` for grouped alerts and labels.

3. **Cluster.** Group by `alertname` + `cluster`. Classify each group:
   - *recurring*: ≥3 occurrences, same shape — the toil candidates;
   - *one-off significant*: long duration or multiple grouped alerts;
   - *noise*: short-lived, auto-resolved (`resolved_by: null`), no discussion.

4. **What humans concluded.** `x_slack_list_channels` — incident channels
   are `inc-<date>-<slug>`, alert feeds `alerts-<cluster>`. For each non-noise
   group: `get_channel_history` (bounded by the window), `get_thread_replies`
   on parents with replies, `search_messages` for the alertname when no channel
   maps. Extract: diagnosis, mitigation, named action items (ticket ids),
   repeated manual fixes, and frustration signals ("again", "toil", "stopgap").
   Estimate human-hours from reply spans and participant counts; use stated
   figures when present.

5. **Correlate evidence.** For each recurring or significant group, confirm the
   story with `x_workload-monitoring_query_range` (e.g.
   `container_memory_working_set_bytes{...}` for OOM patterns,
   `up{job="kubelet",...}` for flaps) and `get_pod_logs` for the implicated
   pod. `list_alerts` gives Alertmanager's view including active silences — a
   silence on a still-flapping alert is a finding, not a fix.

6. **Produce the review** in this order:
   - **Top recurring alerts** — count, trend vs. prior window, cluster/workload,
     root cause if known, human response each time.
   - **Significant incidents** — one paragraph each: timeline, root cause,
     mitigation, human-hours, open action items.
   - **Noisy / silenceable candidates** — false positives and auto-resolving
     blips; for each: evidence it never indicated real impact, and whether a
     silence already exists (then: fix the rule, don't extend the silence).
   - **Action items** — concrete, each backed by evidence and existing tickets;
     flag items agreed in Slack but not done (the "stopgap nobody picked up").

Keep the review short: counts and evidence, no narration. One line per noise
alert. The recurring-toil section is the headline — lead with what pages
humans repeatedly for a known cause.
