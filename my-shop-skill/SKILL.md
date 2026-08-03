---
name: my-shop-skill
description: Use this when somebody asks you anything about my-shop to find services of the shop system.  
---

# my-shop checkout service — agent context

## Where to find the checkout deployment

- **Installation (MC):** `graveler`
- **Workload cluster:** `my-shop`
- **Namespace:** `my-shop`
- **Deployment:** `my-checkout-hello-world`
- **Container:** `hello-world`

The deployment is deployed **directly on the WC** (not via the GS App Platform / App CR on the MC). Do not waste time searching for an App CR named `my-checkout` on `graveler` — it does not exist.

## How to find it in Prometheus

Query Mimir on `graveler-mcp-prometheus` (no `org_id` needed, use the default `giantswarm` tenant) with `namespace="my-shop"`, for example:

```promql
kube_pod_status_phase{namespace="my-shop"}
kube_pod_container_status_restarts_total{namespace="my-shop"}
kube_pod_container_status_last_terminated_reason{namespace="my-shop"}
```

# Rule for readbility

- As a general rule drop the "hello-world" in any communication with me, even if it is part of the deployment or container name. I don't want to see Hello-World.
