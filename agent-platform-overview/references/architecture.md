# Architecture

Public page: https://docs.giantswarm.io/overview/agent-platform/architecture/

## The request path

```
MCP client (IDE, portal, chat, agent) --HTTPS /mcp--> Edge Gateway --> agentgateway --> Muster --> MCP servers
```

- **Edge Gateway**: TLS termination, public hostname. A Kubernetes Gateway API gateway — the
  cluster's shared Envoy Gateway on Giant Swarm installations, an existing Gateway or one the chart
  creates elsewhere.
- **agentgateway**: the MCP data plane. Every `/mcp` request passes through it, so this is where
  tool calls become observable (protocol, tool name, session, latency) and where policy applies. It
  forwards the caller's bearer token to Muster unchanged. It also carries the gRPC route to the
  agent runtime's controller (`agentgateway.<domain>`), behind a JWT policy that verifies the
  caller's Dex token.
- **Muster**: the authentication enforcement point and the aggregator. An unauthenticated request
  gets `401` with `WWW-Authenticate` pointing at OAuth discovery metadata — how MCP clients find
  out where to sign in. Authenticated requests reach the aggregator, which fans out to the servers
  and handles their credentials for the person (forwarding or exchanging the token).
- **MCP servers**: the tools. Two platform groups ship with it (Infrastructure, Agent Platform);
  everything else is a Registered server.

OAuth endpoints (sign-in, token, discovery) are served by Muster directly; only MCP traffic flows
through agentgateway.

## The three "gateways"

The word means three use cases, kept distinct:

| Use case | Purpose | Today |
|---|---|---|
| MCP gateway | authenticated tool access | Muster behind agentgateway |
| LLM gateway | model access, routing, cost | direct provider access, or model-manager's served models (KServe/vLLM speaking the Anthropic and OpenAI protocols) |
| Agent-communication gateway | talking *to* agents: A2A, human-to-agent bridges | agentgateway's gRPC route to kagent; klaus-gateway for Slack |

There is also a product literally named *agentgateway* (Solo.io / Linux Foundation) that serves all
three; in the docs "agentgateway" means that product.

## The agent plane (kagent API v2)

The runtime is the `giantswarm/kagent-upstream` line of the kagent project (upstream `main` at a
pin plus carried patches, released as `v0.11.0-gs.N`) on **Agent Substrate**
(`giantswarm/substrate`). The resources, all in the `kagent` namespace of the management cluster:

| Resource | Role |
|---|---|
| `Harness` (`kagent.dev/v1alpha3`) | One runtime adapter with a digest-pinned workload image and a Substrate policy (worker pool, snapshot policy). The platform ships one Harness, `kagent` — the Go ADK runtime. It admits `AgentTemplate`s by the label `agent-platform.giantswarm.io/harness: kagent` |
| `AgentTemplate` | What an agent is: `systemPrompt`, `modelConfig`, `skills[]` (each pinned to a git commit or an OCI digest), `tools[]` (bindings to `RemoteMCPServer`s or to other templates), `context.compaction`. Its `status.harnesses[]` carries the Harness's verdict: `Accepted`, `ResolvedRefs`, `Compatible`, `Ready` |
| `RemoteMCPServer` | A tool server the runtime connects to. Every tooled agent has one named after itself, pointing at Muster's in-cluster URL with the `X-Muster-Toolset` header (`headersFrom`). Labelled `kagent.dev/discovery: disabled` — the controller holds no user token, so tools resolve at run time as the person |
| `ModelConfig` | Provider, model and the Secret with the key. Platform-owned; agents reference one by name (`default-model-config`) |
| `AgentInstance` | A conversation: one rooted template tree, one A2A context, one Substrate actor. A gRPC resource in Postgres, not a CRD |

**Compile and boot.** When a template is admitted, the Harness compiles it: the runtime boots once
on a worker pod of the pool (`kagent-default`), materialises the skills (git checkout at the pinned
commit, or the OCI image), and Substrate takes the **golden snapshot** of the booted actor. The
template turns `Ready`. A change to prompt, skills, tools or model produces a new revision and a
new golden snapshot; the previous one is collected.

**A turn.** The client (portal, klaus-gateway) creates or resumes an `AgentInstance` and sends an
A2A message with the person's Dex token. Substrate restores the actor from its snapshot onto a free
worker (about a second), the runtime runs the model loop — model calls to the provider, tool calls to
Muster with the forwarded token and the toolset header, skill loads from `/skills` — and streams the
answer back. Where the person has to answer (a question, a tool approval), the task pauses at
`input-required`.

**Between turns.** A turn that ends (completed, failed, cancelled) suspends the actor: its
checkpoint is uploaded to the snapshot store and the worker is freed. A turn that waits for a
person pauses the actor: since Substrate `v0.0.30-gs.3` the pause is copied to the store within a
second, and kagent additionally suspends a pause older than two minutes, so a waiting session
survives the loss of its node. A session whose runtime state was lost before that fails fast with
`runtime lost` and can be deleted; the portal offers a new session with the message carried over.

**Where state lives.**

| Piece | Where | Survives a node loss |
|---|---|---|
| Transcript: tasks, events, history | kagent's Postgres (`kagent_v2`) | yes |
| Runtime state: the harness process image, its conversation memory, `/data` | a Substrate snapshot of the actor in the snapshot store (S3-compatible; on Azure through s3proxy) | yes once uploaded |
| The actor record | Substrate's Postgres | yes |

**Workers.** The worker pool runs on Karpenter nodes (spot on Giant Swarm installations, with a
PodDisruptionBudget); a snapshot is CPU-generation specific, so the pool is pinned to one CPU
vendor and generation. Placement is pool labels plus random choice among free workers.

**Context compaction.** The `agent` chart renders `spec.context.compaction` by default
(`tokenThreshold: 24000`, `eventRetentionSize: 4`): before a model call whose prompt passed the
threshold, everything but the last four events and the turn's question is replaced by one rolling
summary, written by the agent's own model unless a cheaper `summarizer.modelConfig` is named.
A summary is a model call of a few seconds, once per crossing. Prompt prefixes are cached across a
turn's calls.

**Identity on this path.** The only credential on the agent path is the person's token; the
runtime propagates it to Muster (`KAGENT_PROPAGATE_TOKEN`). A forged or expired token fails the
actor's MCP session initialisation with `Unauthorized` — the security property, not a bug.

## Supporting services

- **Valkey** stores Muster's OAuth session state and downstream tokens, so sign-ins survive a
  Muster restart.
- **The avatar service** renders each agent's icon deterministically from its name; portal and
  Slack reuse it.
- **Postgres** (CloudNativePG) for kagent's sessions and Substrate's actor records, with
  Barman backups.

## Fleet-wide aggregation

For a customer with several management clusters, a **central** Muster aggregates the Infrastructure
servers of every cluster: one SSO login, one endpoint. The per-cluster servers share a tool
**family** (`kubernetes`, `prometheus`, `capi`) with the instance argument `management_cluster`,
so `x_kubernetes_list` appears once and the argument selects the cluster (its value is the full
server name, `<mc>-mcp-kubernetes`). Where the remote cluster runs its own Dex, Muster obtains a
token that cluster accepts with RFC 8693 token exchange — still the person's identity, still that
cluster's RBAC. Private clusters are reached through Teleport tunnels (tunnelport).

## Workflows cut agent token cost

Muster packages a multi-step operation as a named **workflow** (`Workflow` resource), registered as
a `workflow_<name>` tool an agent calls once. Muster runs the steps server-side and returns one
shaped document. A paired trial on four real alerts (same agent, model and prompt; raw tools vs the
matching workflow):

| Metric | Raw tools | Workflow | Reduction |
|---|--:|--:|--:|
| Cost | $4.32 | $1.57 | 2.8× |
| Messages | 334 | 71 | 4.7× |
| Cache-read input tokens | 11.0 M | 1.1 M | 9.6× |
| Tool calls | 68 | 4 | 17× |

Cache-read tokens dominate the bill, so the 10× there is the real lever. The trade-off is scope:
a workflow checks what it was written to check. Authoring rules are in the `agent-platform-tools`
skill (`references/workflows.md`).

## Delivery: one chart

`giantswarm/agent-platform` renders every component as a Flux `OCIRepository` + `HelmRelease` with a
semver range, so a component release reaches every installation at the next reconcile with no PR.
Where the cluster has no Flux the chart brings the engine (Flux Operator + `FluxInstance`) and then
manages itself through it. Operators change settings in one values Secret
(`agent-platform-values`); a customer who wants a fixed release pins every component in a
bill-of-materials values file. Giant Swarm management clusters install it through their own Flux
from `management-cluster-bases`, with installation-specific values in the installation's directory
of its management-clusters repository. Agents, MCP servers, model configs and secrets that belong to
an installation live there too (`management-clusters/<mc>/extras/agent-platform/`).
