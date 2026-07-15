# Alerting and silences

Good alerting pages a human only when a human needs to act, and gives them enough
to start acting immediately. This reference covers alert-rule quality and the
lifecycle of silences in an Alertmanager-style router.

## Alert-rule quality

An alert that pages someone should meet all of these:

- **Actionable.** There is something a responder can do. If nothing can be done,
  it is a dashboard signal, not a page.
- **Symptom-based where possible.** Alert on user-visible symptoms (errors,
  latency, unavailability) rather than every internal cause. Cause-based alerts
  are useful as secondary signals but tend to be noisy as pages.
- **Has clear severity/routing.** Page-worthy vs ticket-worthy vs
  informational, routed accordingly.
- **Links to a runbook.** The alert annotation should point to a runbook that
  says what the alert means and how to triage it.
- **Well-tuned thresholds and `for` duration.** Long enough to avoid flapping on
  transient blips, short enough to catch real problems in time.
- **Includes context labels.** Enough labels (service, cluster, namespace,
  environment, severity) to route, group, and silence precisely.

The four "golden signals" — **latency, traffic, errors, saturation** — are a good
default starting set for any service.

### Rule shape (generic Prometheus-style)

Alerting and recording rules are typically defined as `PrometheusRule`-style
resources evaluated by a ruler, which sends firing alerts to Alertmanager:

```yaml
groups:
  - name: example-service
    rules:
      - alert: ExampleServiceHighErrorRate
        expr: |
          sum(rate(http_requests_total{job="example",code=~"5.."}[5m]))
            / sum(rate(http_requests_total{job="example"}[5m])) > 0.05
        for: 10m
        labels:
          severity: page
          service: example
        annotations:
          summary: "Example service error rate above 5% for 10m"
          description: "5xx ratio is {{ $value | humanizePercentage }}."
          runbook_url: "https://runbooks.example.internal/example-service-high-error-rate"
```

Keep alerting and recording rules under version control and deploy them via
GitOps, so changes are reviewed and auditable.

## Silences

A silence suppresses notifications for alerts matching a set of label matchers,
for a bounded time. It does **not** stop the alert from evaluating or firing — it
only mutes the notification. Use silences to keep signal clean during planned
maintenance or an active investigation.

### When to silence

- **Planned maintenance** — you expect specific alerts and do not want to page
  on them.
- **Active investigation** — you already know about the problem and want to stop
  a stream of repeat pages while you work it.
- **Known noisy alert pending a fix** — a short, tracked silence while the rule
  is being tuned (open a ticket to fix the rule, don't silence indefinitely).

Do **not** silence to make a real problem disappear. A silence hides the symptom,
not the cause.

### Silence hygiene

- **Always bound the duration.** Every silence must expire. Prefer the shortest
  window that covers the work; extend deliberately if needed.
- **Match precisely.** Use enough matchers (e.g. `alertname`, `cluster`,
  `namespace`, `service`, `severity`) to mute exactly the intended alerts and
  nothing else. Overly broad matchers hide unrelated problems.
- **Document why.** Record who created it, why, and a link to the related
  incident or ticket.
- **Clean up.** Remove or let silences expire promptly; audit active silences
  regularly so none outlive their reason.

### Two ways to manage silences

- **Interactively** via the Alertmanager UI / API — fast, good for short-lived
  investigation silences.
- **Declaratively** via version-controlled config (GitOps) — auditable and
  reviewable, good for recurring maintenance windows and anything long-lived.

### Matcher example (conceptual)

```
alertname = "ExampleServiceHighErrorRate"
cluster   = "prod-eu-1"
service   = "example"
```

with an explicit end time, e.g. a two-hour window covering a maintenance slot.
