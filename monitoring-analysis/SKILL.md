---
name: monitoring-analysis
description: Use this skill when analysing monitoring data — metrics, logs, Alertmanager state — for a workload or alert: picking the right series, reading patterns (OOM sawtooth, scrape dips), correlating logs with metric events, and presenting findings as evidence.
metadata:
  version: "0.1.0"
---

# Monitoring analysis

How to turn metrics, logs and Alertmanager state into findings. Tool examples
use the muster catalogue names (`x_workload-monitoring_*` via `call_tool`);
the method is tool-agnostic.

## Pick the right series

- **Memory**: `container_memory_working_set_bytes` against the limit — working
  set at exactly the limit means OOM, not load. Pair with
  `kube_pod_container_status_restarts_total` to count the kills.
- **Availability/scrape health**: `up{job=...}` — 0 means the scrape failed,
  not necessarily the target; check more than one job before concluding.
- **Latency**: request-duration series over error counts; a latency spike with
  a disk-sync spike (e.g. etcd WAL fsync) points at storage, not code.
- Query a range (`query_range`) around the event, not just an instant: the
  pattern is the finding.

## Read the patterns

- **Sawtooth to a flat ceiling** (climb → cliff → reset): OOM cycle. The period
  is the leak rate; the ceiling is the limit.
- **Isolated dips in `up`** with healthy service metrics around them: scrape
  failures (timeout, network), not an outage.
- **Step changes** align with deploys or config changes; find the timestamp and
  ask what shipped.
- **Counter resets** (restarts, totals dropping to 0): the pod restarted;
  correlate, don't treat as data loss.

## Correlate before concluding

- Logs at the metric event: `get_pod_logs` for the implicated pod; an
  `OOMKilled`/exit-137 line turns a memory pattern into fact.
- Alertmanager state: `list_alerts` — what fired, what resolved itself, and
  the **silences**. A silence on a still-flapping alert hides toil; check what
  the silence's fix-ticket was and whether it landed before extending anything.
- One source is a hypothesis; two agreeing sources are a finding.

## Present findings as evidence

Per finding: the metric (name + labels), the window, what it shows — one line.

> `container_memory_working_set_bytes{pod="billing-engine-..."}` 10-07→10-13:
> four climbs to 512Mi (the limit), reset after each — OOM cycle, ~48h period.

No prose around it. A finding you cannot back with a series, a log line or an
Alertmanager entry is "not checked", never a guess.
