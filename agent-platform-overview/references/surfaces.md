# Surfaces: where people meet the platform

## The developer portal

Public pages: https://docs.giantswarm.io/overview/developer-portal/agent-platform/ and
https://docs.giantswarm.io/tutorials/agent-platform/create-an-agent/. Giant Swarm's own portal is
the Dev Portal, https://devportal.giantswarm.io; every installation with the platform has a
Backstage of its own with the same section (enabled per instance with the
`page:agent-platform` / `nav-item:agent-platform` extensions).

The **Agent Platform** section:

- **MCP servers** — fleet-wide health of the servers registered with Muster, grouped by management
  cluster and family, from the `MCPServer` resources' status. *Auth Required* is healthy.
- **MCP usage** — tool-call volume, outcomes, latency, top tools and servers, from the gateway
  metrics.
- **Servers** — every server behind the gateway in the three groups, with its auth configuration,
  live tool listing and per-server sign-in, plus a registration wizard.
- **Workflows** — the workflows with steps, validity, statistics, a run button and execution history.
- **Tool explorer** — browse and search every tool, inspect its schema, run it with a generated
  form. Executes what Muster exposes to *you*.
- **Agents** — every agent with readiness, configuration, system prompt, skills, the **Toolset**
  card (the declaration, what it resolves to for you, the labels *Implicit full access* / *No
  tools* / *Full gateway access*), and its owning release. Plus the create flow.
- **Sessions** — your own chat sessions with agents across the fleet: timeline, tool calls, token
  usage, stop, resume, the answer panel for questions and tool approvals. Private to you.
- **Models** — the model configurations per installation with their accepted state; on GPU
  installations the served models, GPU capacity, serve/stop/pull dialogs.

**The create flow** (Agents → create): installation, name (a URL-friendly technical name is derived,
and the avatar renders live), description, model config, system prompt → skills discovered from the
configured repositories → the **Tools** step (opens empty = no tools; presets first, *Read-only
tools* recommended; the catalogue grouped Infrastructure / Agent Platform / Registered servers /
Workflows, with inline sign-in; the resolved list live; up to 32 selectors) → review of the exact
manifests (an `OCIRepository` of the agent chart and a `HelmRelease` with the inline values, plus
the equivalent `helm install`) → deploy **with your token** (RBAC decides) → the agent becomes
Ready once Flux reconciles and the Harness compiles it, typically within a minute.

**Provenance.** GitOps-managed resources are read-only in the portal (the portal hands you the
edited manifest to commit instead). Resources created through the portal or the API are
live-editable. An agent created in the portal is reconciled by Flux but has no file in Git, so it
stays editable there.

**Identity.** The portal forwards your identity on every call: reading uses your token against the
clusters' APIs, tool execution rides your Muster session, deploying applies manifests with your
token. There is no separate portal permission system.

**Sessions in practice.** A turn streams; tool calls show as steps; a question from the agent
opens an answer panel (radio, checkbox, text; Enter sends, Shift+Enter is a newline); *Stop*
cancels the task; a follow-up resumes the same session. A session whose runtime was lost is badged
*Runtime lost* and the composer offers a new session with your text carried over.

## Slack: Swarmgeist

One app, **Swarmgeist**, in the Giant Swarm workspace, is the front door to the agents on the
Giant Swarm Dev Portal installation (backend: `giantswarm/klaus-gateway`). It is for Giant Swarm
staff.

- **Channels**: invite it, then `@Swarmgeist <question>`. It answers in a thread; reply in the
  thread without mentioning it again. A new mention in the channel starts a new conversation.
- **Direct message**: an Agent-type app, so the DM is Slack's agent pane; *New chat* starts a new
  conversation.
- **One conversation = one agent session**; follow-ups keep the context.
- **Sign in once**: the first message gets a *Sign in to Giant Swarm* button (Dex, GitHub or Entra
  connector; the verified email must equal the Slack profile email). Held messages replay after
  the sign-in. ` /login` and ` /logout` (leading space in a DM) exist too.
- **Choosing an agent**: `@Swarmgeist /agent "<display name>" <question>` or `/agent <technical-name>
  …`; `@Swarmgeist /agent` lists the roster with descriptions. Agents are discovered live from the
  platform, so a new agent is selectable the moment it is Ready. The default agent is a platform
  setting (`klausGateway.a2a.defaultAgent`; on the Giant Swarm installation the Swarmgeist agent,
  the platform's read-only explainer, since 2026-09-15 — the SRE Agent is `/agent "SRE Agent"`).
  Switching agents inside a conversation is refused: start a new thread.
- **While it works**: 👀 on your message, then ✅/❌; tool activity as one status line that collapses
  into a receipt (`🛠️ N steps · tool ×k`); `/details full|on|off` per conversation; *Inspect agent
  steps* (⋯ → Apps) shows only you the last tool calls behind recent turns.
- **Tools run as you**: after the sign-in your identity is forwarded through Muster; the audit log
  names you, not a bot. Consent prompts and approval buttons are answered by the initiator.
- **Latency** (Giant Swarm installation, 2026-09): a one-word answer in about 3 s; a question with
  one Kubernetes tool call in 4–7 s; a full cluster-status investigation about a minute.

## IDE and CLI clients

Any MCP client with remote OAuth support connects straight to the installation's Muster:

```json
{ "mcpServers": { "muster": { "url": "https://muster.<installation>.<base domain>/mcp" } } }
```

The client runs the OAuth flow itself. The `muster` CLI (`muster auth login`, `muster auth status`,
`muster call <tool> --json '{…}'`) is the operator's view of the same endpoint and shows per-server
state (`Connected [SSO: Forwarded|Exchanged]`, `Auth Required`, `SSO Pending`). A client that can
set request headers can send `X-Muster-Toolset` by hand to work within a toolset.
Getting started: https://docs.giantswarm.io/getting-started/ai-agent-setup/.

## GitOps

An installation's own agents, MCP servers, model configs and secrets live in its management-clusters
repository under `management-clusters/<mc>/extras/agent-platform/` (`agents/`, `mcpservers/`,
`secrets/` with SOPS-encrypted Secrets). Presets and platform settings live in the installation's
platform values. `kubectl` sees everything the portal sees.
