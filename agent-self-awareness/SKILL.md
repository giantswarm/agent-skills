---
name: agent-self-awareness
description: Use this skill when asked about your capabilities, your foundation, and how to improve your skills.
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

To inspect your own configuration details, you have to find out the cluster and namespace your defining `Agent` custom resource resides in.

## How skills work

Skills are Markdown files with frontmatter. All available skill's name and description automatically get injected into your system prompt, so you know they exist.

You decide when to load a skill's content via the `skills` tool.

## Memory

The recommended way to persist learnings for future agent sessions is to enhance the agent's system prompt or skills.

Declarative agents using the Go ADK runtime have no own method to persist knowledge/memories. Python ADK agents _may_ have memory tools enabled to persist information for a limited time.
