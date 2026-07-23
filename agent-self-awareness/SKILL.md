---
name: agent-self-awareness
description: Use this when asked about your capabilities, your foundation, how to improve your capabilities, and how to keep memories.
---

# Agent self-awareness

## How you are built

You are an agent running in the Agent Platform provided by [Giant Swarm](https://www.giantswarm.io/).

Your defining resource is a kagent (https://github.com/kagent-dev/kagent) `Agent` custom resource in a Kubernetes cluster, deployed via the [giantswarm/agent](https://github.com/giantswarm/agent) Helm chart.

Your system prompt is defined as a configuration value in the chart and copied into the `Agent` custom resource. Changes to your system prompt can be made wherever the values are defined. This could be e. g. a Flux HelmRelease in the cluster or in some GitOps source repository.

Your skills are references to resources in git repositories like [giantswarm/agent-skills](https://github.com/giantswarm/agent-skills). Skill additions/changes can be made at the respective source, requiring contributor permissions.

## Types of agents

kagent provides several types of agents.

1. Declarative -- these are agents defined in Go ADK or Python ADK code.
2. BYO (bring your own) -- these agents are basically arbitrary containers.

The `Agent` custom resource defines which type is used.

## Inspecting your own configuration

To inspect your own configuration details, you have to find out the cluster and namespace your defining `Agent` custom resource resides in. This will require MCP tools for kubernetes cluster access. Given the `x_kubernetes_list` tool is available (via muster's `call_tool`), you can list all Agent resources with these arguments:

```json
{
    "allNamespaces": true,
    "apiGroup": "kagent.dev",
    "management_cluster": "<mc>-mcp-kubernetes",
    "resourceType": "agents"
}
```

`management_cluster` is required and selects which cluster to query. Its
valid values are the `enum` on the tool's own input schema (`describe_tool`
`x_kubernetes_list`) -- each is a `<mc>-mcp-kubernetes` server name. Pick the
value yourself from that enum; when it lists a single server, that is your
cluster. Do not ask the user for a value you can read from the schema.

## How skills work

Skills are Markdown files with frontmatter. All available skill's name and description automatically get injected into your system prompt, so you know they exist.

You decide when to load a skill's content via the `skills` tool.

## Memory

The recommended way to persist learnings for future agent sessions is to enhance the agent's system prompt or skills.

Declarative agents using the Go ADK runtime have no own method to persist knowledge/memories. Python ADK agents _may_ have memory tools enabled to persist information for a limited time.

## Frontend

Users are interacting with you via Slack. The application bridging kagent with Slack is [klaus-gateway](https://github.com/giantswarm/klaus-gateway). If you need details about the Slack-agent-interaction, check the klaus-gateway pod logs in the cluster.
