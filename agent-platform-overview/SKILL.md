---
name: agent-platform-overview
description: Use when someone asks what the Giant Swarm Agent Platform is, how it works or how it is built — its components (Muster, agentgateway, the kagent runtime on Agent Substrate, agent-manager, model-manager, the developer portal, Slack), how people talk to agents, how identity and access work, what a session is, or how you yourself run on it. Gives the short answer first; the references carry the depth.
metadata:
  version: "1.0.0"
---

# The Giant Swarm Agent Platform

Public documentation: https://docs.giantswarm.io/overview/agent-platform/ (concepts) and
https://docs.giantswarm.io/tutorials/agent-platform/ (how-tos). Link the matching page when an
answer gets long; the reader can keep going there.

## How to answer

Answer in layers. Give the one-paragraph version first and offer the next layer. Load a reference
in this skill when the question needs it:

| Question is about | Read |
|---|---|
| The request path, the runtime (Harness, AgentTemplate, Substrate actors, sessions, snapshots), fleets, workflows | `references/architecture.md` |
| Sign-in, tokens, per-user tool visibility, RBAC, audit, why agents act as the person | `references/identity-and-security.md` |
| The developer portal, Slack (Swarmgeist), IDE clients, the `muster` CLI — what people see and do | `references/surfaces.md` |
| A term (toolset, preset, Harness, actor, golden snapshot, session, workflow, family, …) | `references/glossary.md` |

Tools, toolsets and presets are their own skill (`agent-platform-tools`); creating and changing
agents is `agent-platform-agent-management`; writing skills is `agent-platform-skill-authoring`.

## The platform in one paragraph

The Agent Platform is Giant Swarm's open, sovereign environment for running AI agents in
production, on the customer's own Kubernetes clusters. It has two capabilities on one foundation:
**governed tool access** — every tool call, from an IDE, the portal, Slack or an agent on the
cluster, goes through one gateway path (agentgateway in front of **Muster**, the MCP aggregator that
enforces authentication and fans out to the MCP servers behind it) — and an **agent runtime** that
runs agents as Kubernetes resources, versioned as one unit (prompt, toolset, skills, model), and
surfaces them in the developer portal and in chat. The foundation is the cluster and the customer's
existing identity provider: single sign-on, Kubernetes RBAC and GitOps apply to agents exactly as
they apply to people. An agent never holds a credential of its own on the tool path; it acts with
the identity of the person it works for.

## The components

| Component | What it does |
|---|---|
| **Muster** | The MCP gateway: aggregates every MCP server behind one OAuth-protected endpoint, enforces authentication, forwards or exchanges the caller's token downstream, exposes eleven meta-tools, runs workflows, evaluates toolsets |
| **agentgateway** | The MCP data plane in front of Muster and the gRPC path to the agent runtime: the observability and policy choke point; forwards the caller's bearer token without consuming it |
| **Edge Gateway** | TLS termination and the public hostnames (`muster.<domain>`, `agentgateway.<domain>`, the portal). On Giant Swarm installations the cluster's shared Envoy Gateway |
| **Dex** | The installation's OIDC identity provider, federating to the customer's upstream (GitHub, Entra ID, Google, …). The sole token authority: nothing on the platform mints its own identity tokens |
| **Agent runtime** | kagent API v2 (`kagent.dev/v1alpha3`): a controller with `Harness`, `AgentTemplate`, `ModelConfig` and `RemoteMCPServer` resources, a gRPC/A2A API, sessions in Postgres. Runs every agent as an actor on **Agent Substrate** — a pool of warm, sandboxed worker pods (gVisor) with checkpoint/restore |
| **agent-manager** | Agent Platform server: creates, updates, inspects and deletes agents as the caller, exposed as `x_agent-manager_*` tools through Muster and used by the portal's create flow |
| **model-manager** | Agent Platform server: the models an installation serves and the `ModelConfig`s agents run on; on GPU installations it serves models through KServe/vLLM |
| **mcp-kubernetes, mcp-capi, mcp-prometheus** | Infrastructure servers: a management cluster's Kubernetes resources, Cluster API objects and metrics through MCP, one instance per cluster, federated into one tool family each |
| **Developer portal** | The Agent Platform section of the installation's Backstage: servers, tool explorer, workflows, agents (with the create flow), sessions, models. Giant Swarm's own is the Dev Portal at https://devportal.giantswarm.io |
| **klaus-gateway** | The Slack front door (the **Swarmgeist** app in the Giant Swarm workspace): threads become sessions, replies come back under the agent's name, tools run as the person after a one-time sign-in |
| **Valkey** | Muster's OAuth session and token store |
| **Avatar service** | Renders every agent's identifying icon deterministically from its name (`https://avatars.<domain>/v1/<name>.png`) |

Everything ships as **one Helm chart**, `giantswarm/agent-platform`: an app-of-apps that renders one
Flux `HelmRelease` per component with a version range, brings Flux where the cluster has none, and
keeps itself and every component current. Every Giant Swarm management cluster runs it through its
own Flux; a customer's cluster, a kind cluster or a homelab installs it with one `helm install`.

## Three groups of MCP servers

The portal, the tool explorer, the presets and the docs use the same three names:

- **Agent Platform** — the platform's own management surface: agent-manager, model-manager and
  Muster's `core_*` tools. For platform administrators and the agents that run the platform for them.
- **Infrastructure** — the servers for the management clusters underneath: mcp-kubernetes,
  mcp-capi, mcp-prometheus. Across a fleet each family appears once, with `management_cluster`
  selecting the cluster.
- **Registered servers** — everything an installation or a person registers: issue trackers,
  source control, chat, internal services, vendor APIs. Where the customer's own tools live.

## How people reach agents

- **Developer portal** → Agent Platform → Agents: pick an agent, start a session, watch tool
  calls and answer the agent's questions. Sessions are private to the signed-in person.
- **Slack** (Giant Swarm workspace): `@Swarmgeist <question>` in a channel or a DM talks to the
  default agent; `@Swarmgeist /agent "<display name>" <question>` picks one; `/agent` alone lists
  them. One thread is one session. Swarmgeist the Slack app is the front door — the agent behind a
  reply is named on the reply.
- **IDE and CLI**: Claude Code, Cursor, VS Code, the `muster` CLI and any MCP client connect to the
  same Muster endpoint (`https://muster.<installation>.<base domain>/mcp`) as the agents do.

## Identity in five sentences

Every person signs in once through the installation's Dex. The portal, Slack and IDE clients all
forward that person's identity; agents on the platform hold no credential of their own on the tool
path and act with the person's token end to end. Muster shows each person only the tools of the
servers they are signed in to, and each backend's own authorization — Kubernetes RBAC for
mcp-kubernetes, a third-party service's accounts — decides what a call may do. The audit log names
the person, and the platform records which agent acted for them. A **toolset** bounds what an
agent's model can discover and call; it is composition, not authorization, and never widens what
the person may reach.

## How an agent is built and runs

An agent is a **Flux `HelmRelease` of the `agent` chart** (`oci://gsoci.azurecr.io/charts/giantswarm/agent`,
range `1.x`) — created by the portal, by agent-manager or by a GitOps repository. The chart
renders an `AgentTemplate` (prompt, model config, skills, tool bindings, context compaction) and,
unless the agent is chat-only, a `RemoteMCPServer` named after the agent that points at Muster and
carries the toolset as the `X-Muster-Toolset` header. The platform's `Harness` named `kagent` (the
Go ADK runtime) admits the template by label, compiles it into a **golden snapshot** — a booted
actor image with the skills materialised — and the template reports `Ready`.

Every conversation is an `AgentInstance`: one Substrate **actor**, restored from the golden snapshot
onto a worker pod, running the turn in a sandbox. Between turns the actor is checkpointed to the
snapshot store (suspended); while it waits for a person's answer it is paused and copied to the
store within a second. The transcript lives in kagent's Postgres; the actor's memory lives in the
snapshot. A turn's tool calls go from the actor to Muster with the person's forwarded token and the
toolset header. Long turns are compacted (tail retention: when the prompt passes about 24 k tokens
the history is summarised, the last four events stay verbatim).

To look at your own definition: `x_agent-manager_list_agents` (read-only) reports every agent of
the namespace with display name, model config, pinned skills, toolset, readiness and owner; or list
`agenttemplates` in API group `kagent.dev`, namespace `kagent`, with `x_kubernetes_list`
(`management_cluster` is the full server name `<mc>-mcp-kubernetes`, taken from the tool's own
schema). Both through `call_tool`, never as direct function calls.

## Facts to keep straight

- The platform never mints identity tokens. Muster's access tokens are opaque keys into its
  session store; Dex issues every token that carries identity.
- **Auth Required** on an MCP server is healthy: reachable, waiting for a person's sign-in.
  Only `Failed` is an outage.
- The portal is a peer client of the Kubernetes API, not a privileged control panel. What it
  applies, `kubectl` reads back. GitOps-managed resources are read-only in the portal.
- An agent without a toolset has **implicit full access** to whatever the person can reach — the
  behaviour before toolsets existed, made visible. `preset:none` means no tools at all.
- Swarmgeist in Slack is the front door app for every agent; the default agent it hands a bare
  message to is a platform setting (`klausGateway.a2a.defaultAgent`) — on the Giant Swarm
  installation the Swarmgeist agent itself, so a bare `@Swarmgeist` reaches the explainer and
  `/agent "<name>"` any other agent. Slack guests cannot use it, and every participant must be
  signed in before anything is dispatched.
- Machine identity for autonomous agents (no human behind them) is not supported yet; every turn
  has a person.
- Workflows are the platform's cost lever: one `workflow_<name>` call replaces the whole
  discover-query-correlate loop (measured: about 10× fewer cache-read tokens, 17× fewer tool calls).
