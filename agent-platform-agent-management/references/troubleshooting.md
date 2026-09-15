# Troubleshooting an agent

## Where the evidence is

| Layer | Read it with | Shows |
|---|---|---|
| The verdict | `x_agent-manager_get_agent_status` | `ready` / `progressing` / `failed` and the sentence behind it |
| The template | `x_kubernetes_get` on `agenttemplates.kagent.dev` in `kagent` (or `kubectl -n kagent get agenttemplate <name> -o yaml`) | `status.harnesses[]` with `Accepted`, `ResolvedRefs`, `Compatible`, `Ready` (reason and message), `warnings[]` |
| The release | `helmreleases` in `flux-giantswarm` / `kagent` | Helm render errors (an unpinned skill, an empty toolset, schema violations) |
| The worker pod | pods in `kagent` with label `ate.atespace: ate-golden` and `ate.template.name: <agent>-kagent-<12 hex>` (the golden boot), or `ate.actor.name: ai-<instance id>` (a session); `x_kubernetes_logs` with `podName`, `tailLines` | The runtime's own log: skill materialisation, MCP session init, model errors — **the only place a boot failure names its cause** |
| The controller | `kagent-controller` pod logs | Little per template (krt-based v2 controllers do not log reconciles) |
| The portal | Agents → the agent | The same conditions verbatim, the Toolset card with resolution errors |

## Status reasons and their causes

| What you see | Cause | Fix |
|---|---|---|
| `progressing` for up to ~90 s after a create | Flux reconcile plus the golden boot | wait; poll `get_agent_status` |
| `HelmRelease` not Ready, message names a value | the chart refused the render: skill not pinned to a full commit/digest, empty `toolset`, credential on an `http` skill, unknown key | fix the values; `validate_agent` shows the same violations before a write |
| `Accepted=False` | the template is invalid for the Harness (a missing `modelConfig`, a bad binding) | read the message; fix the release |
| `ResolvedRefs=False` `secret "…" not found` | `skillsGitAuthSecretRef` names a Secret that is not in the namespace | create the Secret (key `token`); it recovers on its own |
| `ResolvedRefs=False` on the model config | the `ModelConfig` does not exist or is not `Accepted` (its key Secret is missing) | `list_model_configs`; provide the key or pick another config |
| `Ready=False ActorTemplatePending: waiting for the ActorTemplate golden snapshot` for minutes | the golden actor boots and exits, and the Harness retries every minute without bound; the reason is only in the golden worker pod's log: `fatal: could not read Username for 'https://github.com'` → `failed to materialize Agent Plugins … exit status 128` (a private skill without a credential), a wrong token, a skill path that does not exist at the pinned commit | make the repository public or pin a public one, or (GitOps) add `skillsGitAuthSecretRef`; fix the path/commit |
| `Ready=False`, worker log `field <x> not found in type skill.Frontmatter` | a `SKILL.md` with frontmatter fields outside the agentskills.io set on a kagent line older than `0.11.0-gs.11` | pin a commit without the fields, or move the installation forward |
| `Compatible=False` | a template setting the Harness cannot honour (a Claude/Codex-only field) | remove it; warnings list ignored fields |
| Turn fails at once: `failed to init MCP session: calling "initialize": Unauthorized` | Muster refused the token the actor forwarded — a forged or expired token, or a Dex trusted-issuer audience list that does not admit the token's audiences (a portal reaching another installation's Dex) | the security property working; check the person's sign-in and the installation's `allowedAudiences` |
| Turn fails: `Tool 'x_…' not found` | the model called a backend tool as a function | the meta-tool paragraph in the prompt |
| Every meta-tool call errors naming a preset | the toolset names an undefined preset | define it or change the toolset |
| A new thread fails after 60 s, worker log shows a CPU-feature mismatch | the actor was placed on a worker whose CPU generation differs from the snapshot's | the pool is pinned per vendor and generation; a retry places anew; report if it repeats |
| Session badged *Runtime lost* / `runtime lost` | the paused actor's only state was on a node that is gone (pre `v0.0.30-gs.3` pauses) | delete the session; start a new one — the portal offers it with the message carried over |
| `update_agent` refused: `managed: gitops` | the release is applied from Git | change it in the repository; a `force` write is reverted by Flux |
| `create_agent` refused, lists model configs | unknown `modelConfig` | pick one of the listed |
| `create_agent` refused on `toolset` | missing or empty | at least one selector; `preset:none` for no tools |
| Portal wizard offered a skill the agent cannot fetch | the wizard discovers with a service token; a private repository's skill cannot be fetched by the boot | keep to public repositories through the portal and agent-manager until the credential lands |

## Normal, not a problem

- A fresh create shows a transient `FailedMount … skills-init ConfigMap not found` warning: the
  ConfigMap is created after the pod. Harmless, `progressing`.
- The superseded golden actor of a previous revision lingers until the sweep collects it.
- A `PAUSED` actor a few minutes old (a session waiting for a person) is inside the pause window;
  older ones are suspended to the store by the controller's sweep.
- An MCP server in `Auth Required`.
