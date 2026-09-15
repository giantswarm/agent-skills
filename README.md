# Agent skills

Skills for agents on the [Giant Swarm Agent Platform](https://docs.giantswarm.io/overview/agent-platform/),
written to the [agentskills.io](https://agentskills.io/specification) format and ready to use in
[kagent](https://github.com/kagent-dev/kagent) declarative agents. One directory per skill at the
repository root; the platform's create-an-agent flow and agent-manager discover every `SKILL.md`
here and pin it to a commit on the agent's release.

## Skills about the platform itself

| Skill | For |
|---|---|
| `agent-platform-overview` | What the platform is and how it is built: components, surfaces, identity, how an agent runs |
| `agent-platform-tools` | Muster's meta-tools, toolsets and presets, MCP servers, workflows, missing or refused tools |
| `agent-platform-agent-management` | Creating, changing, inspecting, troubleshooting and deleting agents through agent-manager, the portal or GitOps |
| `agent-platform-skill-authoring` | Writing and reviewing skills like these |

The remaining directories are demo and domain skills (`incident-response`, `k8s-debugging`,
`postmortems`, `agent-self-awareness`, and the fictional customers' data skills).
