---
name: agent-platform-agent-management
description: Use when asked to create, change, inspect, troubleshoot or delete an agent on the Giant Swarm Agent Platform — through agent-manager's tools (x_agent-manager_* via call_tool), the developer portal's create flow, or a GitOps HelmRelease of the agent chart. Covers the technical name, model configs, skills and their pinning, choosing a toolset, writing the system prompt, the status verdicts, and the boot failures and what they mean.
metadata:
  version: "1.0.0"
---

# Managing agents

Public pages: https://docs.giantswarm.io/tutorials/agent-platform/create-an-agent/ (the portal
flow), https://docs.giantswarm.io/overview/agent-platform/toolsets/ (choosing tools). References:

| Topic | Read |
|---|---|
| Every value of the `agent` chart and what it renders | `references/agent-chart-values.md` |
| A GitOps `HelmRelease` for an agent, ready to adapt | `references/helmrelease-example.md` |
| Writing the system prompt: the paragraph every tooled agent needs, the template | `references/system-prompt.md` |
| Status shapes, boot failures, where the evidence is | `references/troubleshooting.md` |

## What an agent is on the cluster

One agent = one Flux **`HelmRelease` of the `agent` chart** (`oci://gsoci.azurecr.io/charts/giantswarm/agent`,
range `1.x`, one shared `OCIRepository` named `agent` per namespace), in the `kagent` namespace,
with the agent's definition as inline values. helm-controller renders an **`AgentTemplate`**
(`kagent.dev/v1alpha3`: prompt, model config, pinned skills, tool bindings, compaction) and — unless
the toolset is exactly `["preset:none"]` — a **`RemoteMCPServer`** named after the agent, pointing
at Muster with the `X-Muster-Toolset` header. The platform's `Harness` `kagent` admits the template
by label, compiles a golden snapshot and reports `Ready`. Three doors write the same thing: the
portal's create flow, agent-manager's tools, a GitOps repository. **Confirm every choice you make
for the person** — the technical name above all — before writing.

## The agent-manager tools

Ten read-only and write tools, exposed by Muster as `x_agent-manager_*`, called as the person
(`writesAsCaller`), each through `call_tool`:

```json
{"name": "x_agent-manager_create_agent", "arguments": {"name": "…", "modelConfig": "…", "toolset": ["…"]}}
```

| Tool | Use |
|---|---|
| `get_info` | Call first: chart range and resolved version, managed namespaces, Harness name, Muster URL, the skill repositories, capabilities |
| `list_model_configs` | The `ModelConfig`s of the namespace with provider, model and `accepted` |
| `list_skills` | Every `SKILL.md` in the configured repositories (`https://github.com/giantswarm/agent-skills` on Giant Swarm installations) with name, description, path, ref and the head commit — the commit a skills entry pins. `repository`, `ref`, `refresh` narrow or refresh |
| `list_agents` | Every agent of the namespace: display name, description, model config, pinned skills, toolset (or `implicitFullAccess: true`), readiness, the owning release and how it is managed (`helmrelease` writable here; `gitops` read-only without `force`; `none` a bare template) |
| `get_agent` | One agent in full, including the release's values |
| `get_agent_status` | One verdict — `ready`, `progressing`, `failed` — with the sentence behind it, folded from the template's Harness conditions, the release and the pods |
| `validate_agent` | Dry run of a create (or of an update with `update: true`): composes the manifests, checks the name, the model config, the toolset, pins the skills, validates against the chart schema; returns the manifests and every violation. Nothing is written |
| `create_agent` | Writes the release (and the shared `OCIRepository` if missing). Requires `name`, `modelConfig`, `toolset`. Refuses an unknown model config (lists the valid ones), an empty toolset, a `runtime` argument, a `gitAuthSecretName` |
| `update_agent` | Merges the given fields into the release values: `skills` and `toolset` replace their whole list; `""` clears a field to the chart default; `refreshSkills: true` re-pins every git skill to its default-branch head. Refused for `gitops`-managed or suspended releases unless `force: true` |
| `delete_agent` | Removes the release; keeps the shared `OCIRepository` while other agents use it. Refused for `gitops` without `force` |

The working shape: `get_info` → `list_model_configs` and `list_skills` → `validate_agent` →
`create_agent` → poll `get_agent_status` until `ready` (about a minute; the golden snapshot is the
long part) → a first turn as the person → `update_agent` for follow-ups.

## The choices and their rules

- **Technical name** (`name`): DNS-1123, max 63 characters, the name of the release, the template
  and the `RemoteMCPServer`, and the seed of the avatar. Chosen by the person, never derived from
  the display name in silence. `displayName` is the friendly, Unicode name (max 63); `description`
  says what the agent is for (the Slack roster and the portal show it).
- **Model config**: one of `list_model_configs`; on Giant Swarm installations `default-model-config`
  (Claude Sonnet) and often a stronger one (`anthropic-opus-5`). Never invent one — an agent on a
  missing or not-accepted config never boots.
- **Toolset**: required; the smallest that does the job. `["preset:read-only"]` for agents that
  answer questions and investigate; `["preset:none"]` for chat-only agents whose knowledge is in
  their skills; `["preset:agent-platform"]` for agents that manage the platform; `["preset:full"]`
  only on an explicit request, since it is everything the person can reach. Add a server or a
  workflow by exact name (`server:mcp-kyverno-playground`, `workflow:pod-health`). Details and the
  failure behaviour: the `agent-platform-tools` skill.
- **Skills**: entries `{name, path, git: {url, commit | ref}}` or `{name, oci}`; what is written is
  always a pin (a ref resolves to its head commit at write time; a tag to its digest). Public
  repositories only through agent-manager and the portal — a private repository's skill fails the
  golden boot with `could not read Username for 'https://github.com'` because neither passes a
  credential; a GitOps release can carry `skillsGitAuthSecretRef.name` (a Secret in `kagent` with
  key `token`). Every agent on the platform may take `agent-platform-overview`,
  `agent-platform-tools`, `agent-platform-agent-management` and `agent-platform-skill-authoring`
  from `giantswarm/agent-skills` when it should explain or operate the platform.
- **System prompt**: focused on role, voice and rules; knowledge goes into skills. Every tooled
  agent's prompt carries the Muster meta-tool paragraph from `references/system-prompt.md` — a
  runtime that is handed `x_kubernetes_list` as a function name fails the turn.
- **Icon**: `iconUrl` = `https://avatars.<base domain>/v1/<name>.png` where the installation
  serves avatars (`https://avatars.gazelle.awsprod.gigantic.io/v1/<name>.png` on the Giant Swarm
  Dev Portal installation); the portal shows it.

## Changing and removing

- A change is a new revision of the whole unit: `update_agent` (portal-created agents) or a new
  commit (GitOps agents). The Harness compiles a new golden snapshot; running sessions keep their
  actor, new sessions start from the new revision.
- **GitOps-managed gets a pull request, ad-hoc gets a live write.** `list_agents` says which is
  which; the portal shows the Git source and refuses live edits and deletes on it. Never `force`
  a write onto a GitOps release to "help" — Flux reverts it and the audit trail is misleading.
- `delete_agent` removes the release; the template and `RemoteMCPServer` go with it, sessions'
  transcripts stay in Postgres, running actors are collected. Delete only on an explicit request
  that names the agent, and one at a time.

## Status: what Ready means and how long it takes

`get_agent_status` folds four sources: the template's `status.harnesses[]` conditions (`Accepted`,
`ResolvedRefs`, `Compatible`, `Ready`), the `HelmRelease` conditions, the release's readiness and
recent warnings. Normal: `progressing` for 20–90 s after a create (Flux reconciles within seconds
when triggered, the golden boot takes the rest), then `ready`. Anything at `Ready=False` for more
than a few minutes is a failure — the table in `references/troubleshooting.md` maps the reason to
its cause. The one that hides best: `Ready=False ActorTemplatePending: waiting for the
ActorTemplate golden snapshot` for ever, whose cause is only in the worker pod's log (a skill fetch
that fails, a Secret that is missing, a prompt-less template) while the Harness retries the boot
every minute without bound.
