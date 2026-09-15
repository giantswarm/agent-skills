# Workflows

Public pages: https://docs.giantswarm.io/tutorials/agent-platform/authoring-workflows/ (the fields)
and https://docs.giantswarm.io/tutorials/agent-platform/saving-tokens-with-workflows/ (the economics).

## Execution model

A `Workflow` (`muster.giantswarm.io/v1alpha1`, namespace `muster`) is an ordered list of steps
Muster runs server-side, returning one JSON document; Muster registers it as `workflow_<name>`.
Each top-level step is exactly one of a `tool` call, a `forEach` loop or a `parallel` group; an
`onFailure` block runs best-effort cleanup. Every step's result is available to later steps and to
the output template as `{{ .results.<id>.<field> }}`; what the *agent* gets back is controlled
separately. Control flow needs Muster ≥ 0.8.0.

## A complete read-only example

```yaml
apiVersion: muster.giantswarm.io/v1alpha1
kind: Workflow
metadata:
  name: pod-health
  namespace: muster
spec:
  description: >-
    Pod health digest for a management cluster. Answers "check the pods in
    <mc>" and "are any pods failing on <mc>?". Lists not-running pods and
    BackOff events in one pass. Stop when the result is empty: no not-running
    pods and no BackOff events means the cluster is healthy, so write a
    one-line "all pods healthy" summary and stop. If a pod is crash-looping,
    you may make one follow-up call to read its logs with tailLines 30.
  args:
    management_cluster:
      type: string
      required: true
      description: The full MCP server name, for example my-cluster-mcp-kubernetes.
  steps:
    - id: not_running
      tool: x_kubernetes_list
      args:
        management_cluster: "{{ .input.management_cluster }}"
        resourceType: pods
        allNamespaces: true
        fieldSelector: "status.phase!=Running"
        output: slim
        limit: 25
      output: true
    - id: backoff_events
      tool: x_kubernetes_list
      args:
        management_cluster: "{{ .input.management_cluster }}"
        resourceType: events
        allNamespaces: true
        fieldSelector: "reason=BackOff"
        fullOutput: true
        limit: 10
      output: true
      allowFailure: true
```

## The fields that matter

- **`spec.description` is the only text the agent sees** (max 1000 characters). Step-level
  descriptions never reach it. Three blocks belong in most descriptions: a *stop-when-healthy
  rule*, a *pinned follow-up rule* (the one extra call allowed, with its arguments), an
  *event-noise hint* (which objects matter).
- **Discoverability**: `filter_tools`' description filter is a case-insensitive **substring**
  match — no stemming, no synonyms. Lead with the topic keyword *and* the natural question.
- **`args`**: typed (`string`, `integer`, `boolean`, `number`, `object`, `array`), `required`,
  `default`, `description`; validated before the first step. A missing required argument fails
  immediately; extra arguments are tolerated.
- **`output: true`** on a step puts its data in the returned document; without it only
  `{id, tool, status}` is emitted. `store: true` is the deprecated name. The last step's result is
  merged into the top level regardless.
- **`spec.output`**: a templated map rendered once after every step, **replacing** the default
  response with the shape you define — the strongest token lever. Reads `.input`, `.results`,
  `.vars`; preserves JSON types (a bare reference stays an array, `{{ len … }}` is a number). With
  it, per-step flags no longer affect the document (Muster logs which flags went inert). A render
  error still returns every step result plus `output_error`.
- **`_debug: true`** as an execution argument returns the full response with every step result
  and the rendered template under `output` — for inspecting a template without removing it.
- **`allowFailure: true`** on legitimately optional steps (a resource type not every cluster has,
  `x_prometheus_*` on a cluster without it, an RBAC-dependent list) — otherwise one error fails the
  workflow and sends the agent chasing it.

## Control flow

- **`forEach`**: `items` must resolve to an array; `as` names the item (`{{ .vars.<as> }}`,
  `{{ .vars.<as>_index }}`); a flat body of sub-steps runs per item sequentially; after the loop
  `{{ .results.<sub> }}` is the last iteration and `{{ .results.<sub>_<n> }}` every iteration. A
  loop multiplies cost — the per-step budgets apply to every iteration.
- **`parallel`**: sub-steps run concurrently and join before the next top-level step; latency is
  the max, not the sum. For fanning out independent reads.
- **`onFailure`**: cleanup steps when a step fails.

## Design rules that keep an agent cheap

1. Shape a tight response: `spec.output` first, `output: true` only where needed, and `limit` /
   `output: slim` on the tools themselves.
2. Put the stop-when-healthy rule in the description — this alone has swung a probe by an order of
   magnitude.
3. Pin the follow-up: name the one call and its arguments.
4. Keep steps read-only where the workflow is diagnostic — then `preset:read-only` includes it.
5. Prefer one workflow per question over one generic workflow with many branches; a long chain of
   raw tool calls in one turn can also drop with a streaming network error, which a workflow avoids.

## Lifecycle

`kubectl apply` the resource (or `core_workflow_create` through Muster); Muster reconciles within
seconds and the agent's next `filter_tools` sees `workflow_<name>`. Iterate live, then manage it
through GitOps. Execution history: `core_workflow_execution_list` / `core_workflow_execution_get`;
the portal's Workflows page shows steps, validity, statistics and a run button.
