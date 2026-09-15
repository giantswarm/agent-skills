# The `agent` chart (1.x): values and what they render

Chart: `oci://gsoci.azurecr.io/charts/giantswarm/agent`, source https://github.com/giantswarm/agent.
One release = one agent. It renders an `AgentTemplate` (`kagent.dev/v1alpha3`) and, for a tooled
agent, one `RemoteMCPServer`; never a `ModelConfig`, a Secret or a `Harness` — those are platform-
owned and referenced by name. agent-manager and the portal write only the values the caller set,
so chart defaults reach every portal-created agent.

| Value | Default | Renders / rule |
|---|---|---|
| `agent.name` | release name | Technical name (DNS-1123, ≤ 63) of the template and the `RemoteMCPServer` |
| `agent.displayName` | `""` | Annotation `ui.giantswarm.io/display-name` (≤ 63, Unicode) |
| `agent.description` | `""` | `spec.description` |
| `agent.iconUrl` | `""` | Annotation `ui.giantswarm.io/icon-url` — the portal reads it |
| `agent.systemMessage` | `You are a helpful agent.` | `spec.systemPrompt` (required, non-empty) |
| `agent.harness` | `kagent` | Label `agent-platform.giantswarm.io/harness` — the Harness's selector. A template no Harness admits is created and never Ready |
| `modelConfig.name` | `default-model-config` | `spec.modelConfig.name`, resolved in the template's namespace |
| `context.compaction.enabled` | `true` | `false` renders no `spec.context`: the whole turn stays verbatim |
| `context.compaction.tokenThreshold` | `24000` | Prompt tokens at which tail retention summarises the history before the next call |
| `context.compaction.eventRetentionSize` | `4` | Events kept verbatim when it fires (a tool exchange is two events) |
| `context.compaction.compactionInterval` / `overlapSize` | unset | Sliding window over whole turns; off by default |
| `context.compaction.summarizer.modelConfig` / `promptTemplate` | `""` | A cheaper summariser model; a replacement prompt (must contain `{conversation_history}`) |
| `skills[]` | `[]` | Up to 50 entries `{name, git: {url, commit}, path}` or `{name, oci: <ref@sha256:…>, path?}`. A **full 40/64-hex commit** or a **digest** — a branch, tag or short SHA fails the render. Names unique. Rendered as `spec.skills[].source.{git|oci}` |
| `skillsGitAuthSecretRef.name` | `""` | Secret in the agent's namespace, key `token`; rendered as `credentialRef {name, key: token}` on **every** git skill; requires `https://` URLs. Secret missing → `ResolvedRefs=False`; wrong token → `Ready=False ActorTemplatePending` with git's error in the actor log. Rotate the contents, never the name |
| `muster.enabled` | `true` | Render the `RemoteMCPServer` and bind it |
| `muster.url` | `http://muster.agent-platform.svc.cluster.local:8090/mcp` | The in-cluster Muster endpoint |
| `muster.tools` | `[]` | Empty = bind every meta-tool; a list narrows the binding (with discovery off the Harness may still expose the whole server and warn) |
| `muster.requireApproval` | `false` | `true` pauses the task at `input-required` before every Muster tool call until the person approves (kagent's HITL) |
| `muster.discovery.enabled` | `false` | Off: label `kagent.dev/discovery: disabled`; tools resolve at run time as the person (Muster is an OAuth resource server; the controller holds no user token) |
| `toolset` | unset | List of `preset:` / `server:` / `workflow:` / `tool:` selectors (≤ 32), joined by `,` into the header `X-Muster-Toolset` (`spec.headersFrom` on the `RemoteMCPServer`). **Exactly `["preset:none"]` renders no `RemoteMCPServer` and no binding**; an empty list fails the render; unset renders no header = implicit full access |
| `extraTools[]` | `[]` | Raw `kagent.dev/v1alpha3` bindings appended after Muster: `{mcp: {server: {kind: RemoteMCPServer, name}, tools, requireApproval}}` or `{agent: {name, description, templateRef: {name}}}` |
| `labels` / `annotations` | `{}` | Merged onto the objects |
| `extraAgentSpec` | `{}` | Deep-merged over the curated template spec (wins) — the escape hatch to any `AgentTemplate` field |

What the Harness does with it: on admission the compile materialises the skills and takes the
golden snapshot; a change to prompt, skills, tools, model or compaction is a new revision. Sessions
of the previous revision keep running on their actor.

A `HelmRelease` written by agent-manager or the portal looks like the GitOps example in
`helmrelease-example.md` with only the set keys under `values`, `interval: 10m`, and the shared
`OCIRepository agent` (semver `1.x`) in the same namespace.
