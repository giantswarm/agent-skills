# Glossary

| Term | Meaning |
|---|---|
| **Agent** | A named, versioned definition: system prompt, model config, skills, toolset. On the platform a Flux `HelmRelease` of the `agent` chart that renders an `AgentTemplate` (and a `RemoteMCPServer`). Versioned as one unit; changing anything is a new revision |
| **Agent instance / session** | One conversation with an agent: an `AgentInstance` in kagent (a Substrate actor plus the transcript in Postgres). Started by a person in the portal or in Slack; private to that person |
| **Actor** | Agent Substrate's unit of execution: a sandboxed process on a worker pod that is restored from a snapshot for a turn and checkpointed afterwards |
| **Agent Substrate** | The runtime underneath kagent API v2: pools of warm worker pods (gVisor), checkpoint/restore of actors, a snapshot store. Fork: `giantswarm/substrate` |
| **agent-manager** | Agent Platform server exposing `x_agent-manager_*` tools (create/update/delete/get/list agents, status, validate, list model configs and skills, info). Writes as the caller |
| **agentgateway** | The MCP data plane in front of Muster and the gRPC path to the runtime. Also the name of the upstream product |
| **Chat-only agent** | Toolset exactly `["preset:none"]`: no `RemoteMCPServer`, no meta-tools, just the model with the prompt and skills |
| **Compaction** | Tail-retention summarisation of a turn's history once the prompt passes a token threshold; on by default from the agent chart |
| **Dev Portal** | Giant Swarm's own developer portal, https://devportal.giantswarm.io, connected to every installation. Customers have a portal per installation |
| **Dex** | The installation's OIDC identity provider; the only token authority on the platform |
| **Family** | Several instances of the same MCP server (one per cluster) exposed under one tool name with a required instance argument (`management_cluster`) |
| **Golden snapshot** | The booted, skills-materialised actor image the Harness compiles for an `AgentTemplate` revision; every session starts from it |
| **Harness** | kagent's runtime adapter resource. The platform ships `kagent` (Go ADK). It admits templates by label and reports their readiness |
| **Implicit full access** | An agent whose release has no `toolset`: its requests carry no header and it reaches everything the person can |
| **klaus-gateway** | The Slack front door (Swarmgeist app): threads → sessions, sign-in link, per-message agent branding, tool receipts |
| **Meta-tools** | Muster's eleven tools: `list_tools`, `filter_tools`, `describe_tool`, `call_tool`, `list_core_tools`, `list/get/describe_resource`, `list/get/describe_prompt`. The only MCP surface an agent sees |
| **Model config** | `ModelConfig` resource: provider, model, key Secret. Platform-owned, referenced by name (`default-model-config`) |
| **model-manager** | Agent Platform server for served models and model configs |
| **Muster** | The MCP gateway/aggregator: OAuth resource server, meta-tools, workflows, toolsets, per-user visibility |
| **OBO** | On behalf of: every tool call an agent makes carries the person's identity |
| **Preset** | A named toolset selection in Muster's configuration (`toolsetPresets`), referenced as `preset:<name>`. Built in: `read-only`, `none`, `full`; platform: `infrastructure`, `agent-platform` |
| **Registered server** | Any MCP server an installation or a person registers (no tool-group label) |
| **Resolved tools** | What a toolset selects right now for a given person: toolset ∩ their catalogue |
| **Skill** | A folder with `SKILL.md` (agentskills.io frontmatter) and optional `references/`, `scripts/`, `assets/`, pinned to a git commit or OCI digest and mounted at `/skills/<name>`; name and description go into the system prompt, the body is loaded on demand |
| **Tool group** | Infrastructure / Agent Platform / Registered servers — the label `agent-platform.giantswarm.io/tool-group` on `MCPServer` resources |
| **Toolset** | The selector list on an agent's release (`preset:`, `server:`, `workflow:`, `tool:`), sent as the `X-Muster-Toolset` header, evaluated per request. Composition, not authorization |
| **Workflow** | A `Workflow` resource Muster runs server-side and exposes as `workflow_<name>`; one call replaces a whole investigation loop |
| **`x_<server>_<tool>`** | The exposed name of an external server's tool; `core_*` are Muster's own; `workflow_*` are workflows |
