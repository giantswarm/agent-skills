---
name: agent-platform-tools
description: Use when a question is about the tools agents use on the Giant Swarm Agent Platform — Muster's meta-tools (filter_tools, describe_tool, call_tool), toolsets and presets (read-only, none, full, infrastructure, agent-platform), the x_/core_/workflow_ tool names, MCP servers and their three groups, workflows and why they are cheaper, or why a tool is missing or a call was refused.
metadata:
  version: "1.0.0"
---

# Tools on the Agent Platform

Public pages: https://docs.giantswarm.io/overview/agent-platform/meta-tools/,
https://docs.giantswarm.io/overview/agent-platform/toolsets/,
https://docs.giantswarm.io/reference/muster/toolsets/, https://docs.giantswarm.io/reference/muster/meta-tools/.

Depth in this skill's references:

| Topic | Read |
|---|---|
| Defining presets for an installation: rule shapes, examples, rollout, verification | `references/toolset-presets.md` |
| Writing a workflow: fields, output shaping, control flow, the design rules that keep it cheap | `references/workflows.md` |
| `MCPServer` resources: transports, families, labels, auth modes, custom and third-party servers, states | `references/mcp-servers.md` |

## Muster is the only tool surface

Every agent, IDE and portal session talks to one MCP endpoint, Muster, and sees **eleven
meta-tools** — never the hundreds of tools behind them:

| Meta-tool | Purpose |
|---|---|
| `filter_tools` | Discover cheaply: `pattern` (glob on names), `description_filter` (substring), `query` (natural language, BM25-ranked), `labels`; bounded page (`limit` default 5, `offset`, `total`, `truncated`), one-line `summary` per tool; `include_schema: true` for full schemas; `toolset` to resolve a toolset without the header; `include_presets: true` to list the presets |
| `describe_tool` | The authoritative description and input schema of one tool |
| `call_tool` | Run any tool by its exact `name` with an `arguments` object |
| `list_tools` | Every tool of the caller's catalogue — large; prefer `filter_tools` |
| `list_core_tools` | Muster's built-in `core_*` tools only |
| `list_resources` / `describe_resource` / `get_resource` | MCP resources |
| `list_prompts` / `describe_prompt` / `get_prompt` | MCP prompts |

The discovery recipe: `filter_tools` to shortlist, `describe_tool` on the candidate, `call_tool` to
run it. Look for a `workflow_*` first — a workflow answers a whole question in one call.

**Names.** `x_<server>_<tool>` is an external server's tool (`x_kubernetes_list`,
`x_prometheus_query`, `x_agent-manager_create_agent`); `core_<area>_<tool>` is one of Muster's own
(`core_workflow_list`, `core_auth_login`); `workflow_<name>` is a workflow. Servers in a **family**
(one instance per cluster) appear once and take the instance argument `management_cluster` whose
value is the full server name, `<mc>-mcp-kubernetes` (the valid values are the enum on the tool's
schema). Every one of these names is a `name` passed to `call_tool`, never a function of its own —
a runtime that is handed `x_kubernetes_list` as a function name fails the turn.

## Toolsets and presets

A **toolset** is the short selector list on an agent's release that says which of the gateway's
tools the agent is composed with. It travels as the `X-Muster-Toolset` header on every request the
agent's runtime makes to Muster; Muster evaluates it **per request, statelessly**, as the third
filter on the caller's catalogue (after "which servers is this person signed in to" and "which
workflows are available"). `list_tools`, `filter_tools`, `describe_tool` answer within it;
`call_tool` of a tool outside it is refused with an error naming the toolset.

Selectors: `preset:<name>`, `server:<name>`, `workflow:<name>`, `tool:<name>` — exact,
case-sensitive names, at most 32 inline. Patterns, excludes, the read-only predicate and labels
exist only inside presets. `toolset:<name>` is reserved.

| Preset | Resolves to |
|---|---|
| `read-only` (built in) | every tool its server annotates read-only, plus every workflow whose steps only call read-only tools; since Muster 5.13.0 also the read-only `core_*` tools, `core_auth_login` among them (signing in to a server changes nothing on the platform) |
| `none` (built in) | nothing — a chat-only agent; the chart renders no Muster binding at all |
| `full` (built in) | the whole catalogue, core tools included — the behaviour before toolsets existed, chosen on purpose |
| `infrastructure` (platform) | every server labelled `agent-platform.giantswarm.io/tool-group=infrastructure`: the mcp-kubernetes, mcp-capi and mcp-prometheus families |
| `agent-platform` (platform) | every server labelled `…/tool-group=agent-platform` (agent-manager, model-manager) plus `core_*` — the preset for an agent that manages the platform |

Installations add their own presets in Muster's values (`muster.muster.toolsetPresets`), reviewed
through GitOps; the portal's Tools step lists them with their descriptions. A server registered
through the portal carries no label and belongs to no shipped preset — select it by name.

**Failure behaviour is closed.** A selector that matches nothing (a server the person is not
signed in to, a renamed tool) contributes nothing and `filter_tools` reports it as unmatched. An
**empty toolset is an error** (say `preset:none`). An **unknown preset is an error on every
meta-tool call**, never a silent fall-back to the full catalogue — so a preset is removed only when
no agent names it. A request **without** the header sees the catalogue as before, which is why
IDEs, the CLI and the portal keep working unchanged and why an agent without a toolset shows
*Implicit full access*.

**Composition, not authorization.** The toolset bounds the *model*; the person's identity and the
backends' authorization (Kubernetes RBAC, a service's accounts) stay the boundary. An agent is
always bounded by *its toolset ∩ the person's own access*. The header is client-declared because
the only credential on the agent path is the person's token; when an agent identity exists, Muster
will resolve the toolset from it instead.

## MCP servers

`MCPServer` resources (`muster.giantswarm.io/v1alpha1`, namespace `muster`) register the servers.
On a cluster they are remote (`streamable-http`, `sse`) — `stdio` runs a child process inside
Muster and is for a local `muster serve` only. States: remote `Connected`, `Auth Required`,
`Connecting`, `Disconnected`, `Failed`; stdio `Running`, `Starting`, `Stopped`, `Failed`.
**`Auth Required` is healthy** — reachable, waiting for a person's sign-in; only `Failed` is an
outage and only `Failed`/flapping alerts. The tool-group label sorts a server into Infrastructure
or Agent Platform; no label means Registered server. Tools are discovered when a server starts and
re-registered live — no client restart.

## Workflows

A `Workflow` resource is a list of steps Muster runs server-side (`tool` calls, `forEach`,
`parallel`, an `onFailure` block), returning one JSON document; Muster registers it as
`workflow_<name>`. One call replaces the agent's discover-query-correlate loop: measured on four
real alerts, 17× fewer tool calls and about 10× fewer cache-read tokens. Two rules decide whether an
agent ever uses one: `spec.description` is **the only text the agent sees** (max 1000 characters),
and `filter_tools`' description filter is a **case-insensitive substring match** — so the
description leads with the topic keyword and the natural question ("pod health", "are any pods
failing on <mc>?"), and carries a **stop-when-healthy rule** ("empty result means healthy: write a
one-line summary and stop") plus the one follow-up call the agent may make. A `readOnly` workflow
(steps call only read-only tools) is part of `preset:read-only`.

## When a tool is missing or refused

| Symptom | Cause | What to do |
|---|---|---|
| A server's tools do not appear for this person | not signed in to that server (per-user visibility) | `core_auth_login` for that server, or sign in on the portal's Servers page; `muster auth status` shows `Auth Required` |
| `call_tool` refused, error names the toolset | the tool is outside the agent's toolset | that is the agent's composition; change the agent's toolset (agent-manager `update_agent`), not the call |
| Every meta-tool call errors, naming a preset | the agent's toolset names a preset the installation does not define | define the preset or change the toolset |
| `forbidden` from a cluster | Kubernetes RBAC for the person | bind the identity-provider group to a role on that cluster |
| The agent keeps asking to authenticate | expired session / audience mismatch on a forwarding server | re-login; check `requiredAudiences` on the `MCPServer` |
| A workflow runs by name but the agent never picks it | its description lacks the words the agent searches for | rewrite `spec.description` |
| A workflow returns clean and the agent keeps digging | no stop-when-healthy rule | add it to the description |
| Turn fails "tool `x_…` not found" | the model emitted a backend tool as a function name | call it through `call_tool`; on the Go runtime the mistake is handed back, on the Python runtime it ends the turn |
