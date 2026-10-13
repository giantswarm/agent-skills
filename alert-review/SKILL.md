---
name: alert-review
description: Use this skill to run a periodic (weekly) alert review — "review last week's alerts", "alert review", "what paged us and why" — over PagerDuty incidents, the Slack discussions around them, and monitoring evidence. Starts with a compact overview; drills into an incident when asked.
metadata:
  version: "0.2.0"
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

**First answer: overview only.**
- One headline sentence.
- The week's numbers: total pages, resolved / acknowledged / still open,
  recurring vs one-off vs noise.
- The 2–3 spots worth drilling into, one line each, with the why
  ("billing-engine OOM — 4th page this week, fix agreed but never applied").
- End by offering drill-down ("Ask me about any of these").
- No tables, no per-incident analysis, no metric dumps.

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
3. **Headline candidates.** For the 2–3 non-noise groups, skim
   `x_slack_list_channels` (incident channels `inc-<date>-<slug>`, feeds
   `alerts-<cluster>`) and `get_channel_history` just enough for the one-line
   why. Save the rest for drill-down.

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
