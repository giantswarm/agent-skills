# Defining toolset presets

Public page: https://docs.giantswarm.io/tutorials/agent-platform/toolset-presets/. For platform
teams; agent authors pick presets in the portal's Tools step or in `create_agent`'s `toolset`.

## Where presets live

Muster reads `toolsetPresets` from its configuration, rendered from the Muster chart's
`muster.toolsetPresets` value. The `agent-platform` meta chart forwards its `muster:` block to the
Muster release, so on the platform the key is **`muster.muster.toolsetPresets`** — on a Giant Swarm
installation in the installation's platform values (its `configmap-values.yaml.patch` in the
management-clusters repository), on a self-hosted install in the values Secret. Presets that
select by label need Muster ≥ 5.12.0 (the fleet meta chart pins that floor).

The two platform presets as shipped:

```yaml
muster:
  muster:
    toolsetPresets:
      infrastructure:
        description: The servers for the infrastructure underneath the platform (Giant Swarm installations' management clusters) — mcp-kubernetes, mcp-capi, mcp-prometheus.
        include:
          - label: agent-platform.giantswarm.io/tool-group=infrastructure
      agent-platform:
        description: The platform's own management surface — agent-manager, model-manager and muster's core tools.
        include:
          - label: agent-platform.giantswarm.io/tool-group=agent-platform
          - pattern: core_*
```

## Rule shapes

A preset has a `description`, an `include` list and an optional `exclude` list; it resolves to the
union of its includes minus its excludes. Every rule sets exactly one key:

| Rule | Selects |
|---|---|
| `tool: <name>` | one tool by its exposed name (`x_<server>_<tool>`, `workflow_<name>`, `core_*`) |
| `pattern: <glob>` | every tool whose exposed name matches (`x_mcp-kubernetes_*`, `*_delete`) |
| `server: <name>` | every tool of that `MCPServer` — a family name or a member's name |
| `workflow: <name>` | the workflow's `workflow_<name>` tool |
| `readOnly: true` | every tool annotated read-only, including workflows whose steps only call read-only tools |
| `label: <key>=<value>` or `label: <key>` | every tool of every `MCPServer` carrying that label, read live |
| `preset: <name>` | everything another preset selects (composition; `include` only) |

Excludes take the same shapes except `preset`. `include` is a **union**: `preset: infrastructure`
next to `readOnly: true` selects every infrastructure tool *and* every read-only tool anywhere —
narrow with `exclude`, not by intersecting includes.

## Examples

By server name, without deletes:

```yaml
test-clusters:
  description: The kubernetes and prometheus servers of the test management clusters, without deletes
  include:
    - server: test-01-mcp-kubernetes
    - server: test-02-mcp-kubernetes
    - server: test-01-mcp-prometheus
    - server: test-02-mcp-prometheus
  exclude:
    - pattern: "*_delete"
```

By a label you stamp yourself (label the `MCPServer`s under `metadata.labels`; agent-manager's and
model-manager's charts expose theirs as `muster.mcpServer.labels`):

```yaml
test-clusters:
  description: Every server labelled for the test pipeline
  include:
    - label: example.com/pipeline=testing
```

By composition:

```yaml
infra-triage:
  description: Every infrastructure tool plus the incident-triage workflow, without deletes
  include:
    - preset: infrastructure
    - workflow: incident-triage
  exclude:
    - pattern: "*_delete"
```

## Rules of the road

- Never name a preset `read-only`, `none` or `full` — Muster refuses to start (the meta chart fails
  the render first).
- A preset that matches nothing is not an error; the agent has no tool from it and `filter_tools`
  reports the selector as unmatched.
- Remove a preset only when no agent names it — `x_agent-manager_list_agents` shows every agent's
  toolset. An agent naming a missing preset errors on every meta-tool call.
- Muster validates presets at startup: a rule with no or several keys, a pattern that does not
  compile, `readOnly: false`, an unknown preset in a composition or a cycle stops Muster with an
  error naming the preset and the rule.

## Roll out and verify

Commit the values through GitOps; the change rolls the Muster pod once. Then, with an authenticated
CLI context:

```bash
muster call filter_tools --json '{"include_presets": true, "toolset": ["preset:test-clusters"]}'
```

`presets` lists the built-ins, then the shipped and installation presets with descriptions; `tools`
is what the toolset resolves to for the caller; `toolset_unmatched` names selectors that selected
nothing. A server the caller is not signed in to contributes nothing — the same view an agent
driven by that person gets. An agent can run the same check through
`call_tool(name="filter_tools", arguments={...})`.

## Sending a toolset from any client

Put `X-Muster-Toolset: preset:read-only, workflow:incident-triage` on requests to the gateway. A
header that is empty, names an unknown preset, uses `toolset:` or exceeds 32 selectors gets an
error result on every meta-tool call.
