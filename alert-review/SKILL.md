---
name: alert-review
description: Use this skill to run a periodic (weekly) alert review — "review last week's alerts", "alert review", "what paged us and why" — over PagerDuty incidents, the Slack discussions around them, and monitoring evidence. Starts with a glanceable alert table; drills into an incident when asked.
metadata:
  version: "0.3.0"
---

# Alert review

Review a window of alerts (default: the last 7 days): what paged humans, what
it cost, what to change. Every claim carries its evidence: an incident id, a
Slack channel + ts, a metric, or a log line.

All tools run through muster's `call_tool` with their full catalogue names:
`x_pagerduty_*`, `x_slack_*`, `x_workload-monitoring_*`. Time parameters accept
ISO-8601 or relative offsets like `-7d`.

Write actions (acknowledging/resolving incidents, posting to Slack, creating
silences) may be in your toolset; the review stays read-only — write only when
the user explicitly asks.

## Interaction contract

**First answer: one headline sentence + the alert table.**
- One row per alert group (alertname + cluster), covering **every** group in
  the window — resolved and noise included.
- Columns: alert · cluster · pages · state (open/ack/resolved/silenced) ·
  one-phrase context ("recurring — fix agreed, never applied",
  "silenced until <date> (SIL-7F2A)", "auto-resolved blips").
- Order: needs-a-look first (open, recurring, silenced-but-masking), noise
  last; lead needs-a-look rows with ⚠.
- End by offering drill-down ("Ask me about any of these").
- Banned in the first answer: per-incident analysis, metric dumps.

**Drill-down only on request.** When the person names an alert or incident,
analyse that one: what Slack concluded, the correlated metrics/logs,
engineer-hours, open action items with evidence. One incident per answer,
still condensed — counts and evidence, no narration.

## Gathering (before the overview)

1. **Window.** Default `since: -7d`; say which window you used.
2. **Incidents.** `x_pagerduty_list_incidents {since}` — no filters; the
   review needs the noise too. Group by `alertname` + `cluster`:
   *recurring* (≥3, same shape), *one-off significant* (long or multi-alert),
   *noise* (short-lived, auto-resolved, no discussion).
3. **Row context.** Per non-noise group, one bounded skim for the one-phrase
   context: `x_slack_list_channels` (incident channels `inc-<date>-<slug>`,
   feeds `alerts-<cluster>`) + `get_channel_history`, and
   `x_workload-monitoring_list_alerts` for silence state. Noise rows need no
   skim ("auto-resolved blips"). Save the rest for drill-down.

## Drill-down (on request, per incident)

- `x_pagerduty_get_incident` + `list_alerts_for_incident` for the shape.
- Slack: `get_channel_history` in the window, `get_thread_replies` on parents
  with replies, `search_messages` for the alertname. Extract diagnosis,
  mitigation, named action items (ticket ids), repeated manual fixes,
  frustration signals ("again", "toil", "stopgap"). Engineer-hours from reply
  spans and participants; stated figures win.
- Metrics/logs: confirm with `x_workload-monitoring_query_range` (e.g.
  `container_memory_working_set_bytes{...}` for OOM, `up{job="kubelet",...}`
  for flaps) and `get_pod_logs`. `list_alerts` gives Alertmanager's view with
  silences — a silence on a still-flapping alert is a finding, not a fix.
- Close with the open action items, each backed by evidence; flag what was
  agreed in Slack but never done.
