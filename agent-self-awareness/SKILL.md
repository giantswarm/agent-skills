---
name: agent-self-awareness
description: Use this when asked about your capabilities, your foundation, how to improve your capabilities, and how to keep memories.
---

# Agent self-awareness

## How you are built

You are an agent running in the [Giant Swarm](https://www.giantswarm.io/) Agent Platform.

Your defining resource is a kagent (https://github.com/kagent-dev/kagent) `Agent` custom resource (`api.kagent.dev/v1alpha3`) in a Kubernetes cluster, rendered by one release of the [giantswarm/agent](https://github.com/giantswarm/agent) Helm chart. It has two halves:

- `spec.template` -- what you are: system prompt, model (a `ModelConfig` by name), skills, plugins and tool bindings.
- `spec.harnessRef` -- the `Harness` that runs you, by name. A Harness is of one kind: `kagent` (the kagent Go ADK, the kind of the platform's default Harness, also named `kagent`), `claude` (Claude Code), `codex` or `byo` (an arbitrary image). The name does not tell you the kind; the Harness's spec does (see below).

Your system prompt is the chart value `agent.systemMessage`, copied into `spec.template`. Change it where the release's values are managed: through agent-manager (the portal or `x_agent-manager_update_agent`) or in the GitOps repository that holds the HelmRelease. The `agent-platform-agent-management` skill says which applies to you.

Your skills are pinned to a full commit of a git repository like [giantswarm/agent-skills](https://github.com/giantswarm/agent-skills), or to an OCI digest. Changing a skill requires contributor permissions at its source, and a merged change reaches you only once your release is re-pinned to the new commit or digest.

## Inspecting your own configuration

`x_agent-manager_get_agent` (via muster's `call_tool`) with your technical name -- your `Agent` object's name, not your display name -- returns your HelmRelease values, Harness, pinned skills and plugins, toolset and status. `x_agent-manager_list_agents` lists the agents when you are unsure of the name.

To read the custom resources themselves, list them with `x_kubernetes_list`:

```json
{
    "allNamespaces": true,
    "apiGroup": "api.kagent.dev",
    "management_cluster": "<mc>-mcp-kubernetes",
    "resourceType": "agents"
}
```

`resourceType: harnesses` the same way shows each Harness's kind (`spec.kagent`, `spec.claude`, …) and configuration.

`management_cluster` is required and selects which cluster to query. Its
valid values are the `enum` on the tool's own input schema (`describe_tool`
`x_kubernetes_list`) -- each is a `<mc>-mcp-kubernetes` server name. Pick the
value yourself from that enum; when it lists a single server, that is your
cluster. Do not ask the user for a value you can read from the schema.

## How skills work

Skills are Markdown files with frontmatter. Every available skill's name and description is put into your system prompt, so you know they exist.

You decide when to load a skill's content. On a `kagent` Harness, `load_skill` returns a skill's `SKILL.md`, `load_skill_resource` one of its other files, and `list_skills` lists them. On a `claude` Harness, skills load the way Claude Code loads its own.

## Memory

The recommended way to persist learnings for future agent sessions is to enhance the agent's system prompt or skills.

A `kagent` Harness can enable long-term memory (`spec.kagent.memory`: an embedding model and a `ttlDays` lifetime), which adds memory tools. The platform's default Harness ships without it: read your Harness's spec before assuming you have memory. `spec.kagent.compaction` only summarizes older parts of a long conversation; it does not carry anything into the next session.

## Frontend

Users interact with you through the portal (Agent Platform → Agents) or Slack. The application bridging kagent with Slack is [klaus-gateway](https://github.com/giantswarm/klaus-gateway). If you need details about the Slack-agent-interaction, check the klaus-gateway pod logs in the cluster.
