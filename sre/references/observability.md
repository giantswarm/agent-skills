# Observability

Observability is the ability to understand a system's internal state from its
external outputs. In practice that means three signal types plus the discipline
to turn them into service-level objectives you can defend.

## The three signals

- **Metrics** — cheap, aggregatable numeric time series (request rate, error
  rate, latency percentiles, resource saturation). Best for alerting, trends, and
  SLOs. A Prometheus-style stack (with a scalable backend such as Mimir/Cortex
  /Thanos) is the common pattern.
- **Logs** — discrete, timestamped events with detail. Best for explaining *why*
  something metrics-flagged is happening. Aggregated centrally (Loki/Elasticsearch
  -style) and correlated by labels/time with metrics.
- **Traces** — end-to-end request paths across services. Best for latency
  analysis and understanding cross-service causality in distributed systems.

A collector/agent (OpenTelemetry Collector, Alloy, and similar) typically ships
all three from workloads to their backends. Dashboards (Grafana-style) read the
backends and are where humans look first.

## The golden signals

For any user-facing service, instrument at least:

- **Latency** — how long requests take (track percentiles, and separate success
  from error latency).
- **Traffic** — demand on the system (requests/sec, throughput).
- **Errors** — rate of failed requests (explicit and implicit failures).
- **Saturation** — how full the system is (CPU, memory, disk, queue depth,
  connection pools). Watch the most constrained resource.

For resource-oriented views, the **USE** method (Utilization, Saturation, Errors
per resource) complements the golden signals.

## SLIs, SLOs, and error budgets

- **SLI (indicator)** — a measured quantity that reflects user experience, e.g.
  "proportion of HTTP requests served successfully in under 300 ms".
- **SLO (objective)** — the target for an SLI over a window, e.g. "99.9% of
  requests over 30 days". Set it from what users actually need, not from what is
  trivially achievable or impossibly perfect.
- **Error budget** — `100% − SLO`. The allowed amount of failure. It is a budget
  to *spend*: while budget remains, you can ship and take risk; when it is
  exhausted, priorities shift toward reliability. Error budgets turn "is it
  reliable enough?" from an argument into a measurement.

Alert on **SLO burn rate** (how fast you are consuming the error budget) rather
than on every threshold breach — a fast burn pages, a slow burn tickets.

## Dashboard practices

- **Lead with user-facing signals.** Top of the dashboard = the golden signals
  for the service. Internals go below.
- **One purpose per dashboard.** A service-health dashboard and a
  capacity-planning dashboard are different things.
- **Make "normal" legible.** Show thresholds/SLO lines so a glance tells you if
  the current value is fine.
- **Templating over duplication.** Parameterize by cluster/namespace/service so
  one dashboard serves many targets, rather than copying dashboards per
  environment.
- **Link to context.** From a panel, link to the relevant logs query, trace
  view, alert, or runbook.

## Correlation workflow

When investigating: start from the **metric** that flagged (what and when),
pivot to **logs** filtered to that component and time window (why), and use
**traces** to follow a slow or failing request across service boundaries (where
in the path). Shared labels (service, cluster, namespace) and aligned timestamps
are what make the pivots fast.
