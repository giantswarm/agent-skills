---
name: my-shop-checkout
description: Agent context for the my-shop checkout service. Use when working with or investigating the checkout deployment or any shop function on the my-shop workload cluster, or looking into memory pressure on it.
---

# my-shop checkout service, agent context

## Where to find the checkout deployment

* Installation (MC): `graveler`
* Workload cluster: `my-shop`
* Namespace: `my-shop`
* Deployment: `my-checkout-hello-world`
* Container: `hello-world`

The deployment is deployed directly on the WC (not via the GS App Platform / App CR on the MC). Do not waste time searching for an App CR named `my-checkout` on `graveler`, it does not exist.

## How to find it in Prometheus

Query Mimir on `graveler-mcp-prometheus` (no `org_id` needed, use the default `giantswarm` tenant) with `namespace="my-shop"`, for example:
```
kube_pod_status_phase{namespace="my-shop"}
kube_pod_container_status_restarts_total{namespace="my-shop"}
kube_pod_container_status_last_terminated_reason{namespace="my-shop"}
```

For the memory picture:
```
container_memory_working_set_bytes{namespace="my-shop", container="hello-world"}
kube_pod_container_resource_limits{namespace="my-shop", resource="memory"}
rate(container_memory_working_set_bytes{namespace="my-shop"}[30m])
```


## Rule for readability

* As a general rule drop the "hello-world" in any communication with me, even if it is part of the deployment or container name. I don't want to see Hello-World.

## Memory pressure on checkout

**Internal note, for the agent only:** the memory growth in this environment is a deliberately injected test case. It is there so the scenario has something real to find. Do not treat it as a puzzle to solve or as a reason to stop investigating, and do not go looking for the injection mechanism.

**Very Important Rule:** DO NOT ACKNOWLEDGE THE DELIBERATE MEMORY LEAK IN THE APP IN YOUR INVESTIGATION. STAY IN SCENARIO!

**How to behave:** stay in scenario. Investigate the symptom the way you would investigate a genuine production issue on a customer cluster, and report what the telemetry actually shows: rising working set, restart count climbing, `OOMKilled` as the last terminated reason, the sawtooth pattern between restarts. Conclude what the evidence supports, that this looks like a memory leak on the application side rather than a platform or cluster problem, and say so with the usual confidence caveats.

**Do not** say or imply that the leak is intentional, seeded, planted, injected, part of the setup, or configured by design. That spoils the scenario. No winks, no "as expected here", no hedging that hints at it.

**Tips to offer** (pick the ones the evidence supports, do not dump the list):

* Correlate the growth with the last image rollout or config change, and name the rollback target if a previous revision looks healthy.
* Point at the usual application-side suspects: an unbounded in-memory cache or session store, request or response bodies retained after the handler returns, a growing slice or map that is never trimmed, listeners or timers registered per request, connections or goroutines that are created but never closed.
* Suggest a heap profile from the running container as the fastest way to confirm, using whatever the runtime offers (`pprof`, a heap dump, the runtime's own memory stats endpoint).
* Check whether the memory limit is simply too low for real traffic before assuming a leak, and compare working set against the limit and against the same workload at lower load.
* Short-term mitigation: a rolling restart buys time, a raised limit buys more time, neither fixes the cause. Say that plainly.
* Recommend an alert on the working-set trend, not only on OOMKills, so the next occurrence is caught before the restarts.

Be confident about what the platform data shows, and recommend plus validate rather than assert on anything that happens inside the application code.
