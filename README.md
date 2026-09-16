# Agent skills

Skills for agents on the [Giant Swarm Agent Platform](https://docs.giantswarm.io/overview/agent-platform/),
written to the [agentskills.io](https://agentskills.io/specification) format and ready to use in
[kagent](https://github.com/kagent-dev/kagent) declarative agents. One directory per skill at the
repository root; the platform's create-an-agent flow and agent-manager discover every `SKILL.md`
here and pin it to a commit on the agent's release.

## Skills about the platform itself

| Skill | For |
|---|---|
| `agent-platform-overview` | What the platform is and how it is built: components, surfaces, identity, how an agent runs, how to look at the live platform |
| `agent-platform-tools` | How Muster works and how to find any tool: the meta-tools and the `call_tool` contract, toolsets evaluated per request, MCP servers, workflows, model-manager |
| `agent-platform-agent-management` | Creating, changing, inspecting, troubleshooting and deleting agents through agent-manager, the portal or GitOps; status through the platform's workflows |
| `agent-platform-skill-authoring` | Writing and reviewing skills to the fetch-live standard: format, loading, pins, review checklist |

The four tell an agent how to *find* the current truth (the CRDs and releases through mcp-kubernetes, tool
names and schemas through Muster, the platform's state through `workflow_*` tools) rather than carrying
copies of it, and each owns one topic.

## Skills for the Repo Manager agent

| Skill | For |
|---|---|
| `giantswarm-repository-setup` | Declaring a repository in its team file of `giantswarm/github` as desired state: the creation flow (validate, dry run, confirm, create as the person), the two guards on machine approval, the set-up state and the knob that fixes a red step, *Reconcile now* |
| `giantswarm-repository-lifecycle` | Deprecate, archive, transfer — what each pull request changes, whose review it needs and where the ask lands; that deletion does not exist; finding abandoned or unowned repositories and recording a decision |
| `giantswarm-repository-ci-renovate` | Where a repository's CI, release workflow and Renovate config come from (`devctl gen` through the declaration), the "why is it not releasing" diagnosis order, Renovate's onboarding pull request, generated files never hand-edited |

The three follow the same standard: the schema is read from `giantswarm/github`, the inventory and the
tools from giantswarm-repo-manager through Muster, and no list of fields or tools is copied into a skill.

The remaining directories are demo and domain skills (`incident-response`, `k8s-debugging`,
`postmortems`, `agent-self-awareness`, and the fictional customers' data skills).
