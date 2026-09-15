# Identity and security

Public pages: https://docs.giantswarm.io/overview/agent-platform/security/ (the model),
https://docs.giantswarm.io/overview/agent-platform/authentication/ (every token on the path),
https://docs.giantswarm.io/overview/agent-platform/platform-integration/ (SSO, RBAC, observability),
https://docs.giantswarm.io/tutorials/agent-platform/access-control/ (binding groups to roles).

## One identity provider per installation

The platform uses the installation's OIDC provider — Dex on Giant Swarm clusters, federating to the
customer's upstream (GitHub org and teams, Entra ID, Google, …). The contract is plain OIDC, so any
compliant provider works on a self-hosted install. **The identity provider is the sole token
authority**: Muster signs nothing, no downstream system trusts Muster as an issuer, and every
credential that carries identity is issued and validated by Dex.

## Signing in to Muster

MCP clients use OAuth 2.1 authorization code with PKCE. A first request gets `401` with
`WWW-Authenticate` pointing at Muster's discovery metadata; the client opens the browser at
Muster's `/oauth/authorize`; Muster redirects to Dex; Dex redirects to the upstream provider; the
person types their password **only there**. The chain unwinds with one-time codes; the tokens travel
server to server. Muster hands the client an **opaque** access token — a random key into its own
session store, mapped to the Dex token set (ID, access, refresh). Access tokens last 30 minutes and
refresh in the background; a session lasts about 30 days.

Clients that speak remote MCP with OAuth (Claude Code, Cursor, VS Code, the portal) connect
directly. `muster agent` is a thin local bridge for stdio-only clients.

## Downstream: how a backend gets its authority

Every MCP server behind Muster declares how calls to it are authenticated:

| Mode | What happens |
|---|---|
| `none` | no authentication (anonymous by design) |
| `oauth` | the caller must be signed in; no token is passed on |
| `forward` | the person's own token is forwarded unchanged — servers that trust the same Dex (`auth.forwardToken: true`, with `requiredAudiences` such as `dex-k8s-authenticator`) |
| `exchange` | RFC 8693 token exchange at the target's Dex for a token that cluster accepts — remote clusters with their own identity provider |

The rule: **who administers the backend's account system decides.** Platform-administered backends
(mcp-kubernetes, mcp-capi, mcp-prometheus, agent-manager, model-manager) derive authority from the
person's identity per request. Externally administered backends (a vendor service with its own
accounts) get Muster acting as an OAuth client toward *their* authorization server: the person
grants access once in the browser (`core_auth_login` issues the link) and Muster stores that grant.

When a downstream server answers `401`, Muster returns an "authentication required" result with the
authorization URL; after the browser sign-in the call is retried with the acquired token.

## Per-user tool visibility

Per-user state is keyed on the OAuth `sub` claim. Each person sees only the tools of the servers
they are signed in to; a cluster they cannot reach contributes no tools to their catalogue. The
catalogue an agent's meta-tools see is therefore *the toolset ∩ the person's own access*.

## Kubernetes: RBAC evaluates the person

- **Management clusters**: Muster forwards the person's token to mcp-kubernetes, which passes it to
  the API server's OIDC authentication. RBAC evaluates the person — the same roles and bindings as
  with `kubectl` — and the audit log records the person. No impersonation, no platform-minted token.
- **Fleets**: a central Muster obtains a token the remote cluster accepts via token exchange —
  still the person, still that cluster's RBAC.
- **Workload clusters**: interim — the cluster's admin kubeconfig with user impersonation
  (`mcp-kubernetes` impersonates the person's user and groups), so RBAC still evaluates the person.

Consequence: **an agent cannot do anything the person it acts for could not do.** Granting or
revoking an engineer's cluster permissions changes what agents acting for them can do, immediately;
there is no second permission system. A `forbidden` from a cluster is RBAC, not a platform bug —
bind the identity-provider group to a role on that cluster.

## Agents acting for a person

An agent on the platform holds no identity of its own on the tool path. In the portal and in Slack
it acts with **the person's** token end to end; every downstream system and audit log sees the
person, and the gateway records which agent acted. What the agent can *reach* is the person's
access; what it is *composed with* is its toolset (see `agent-platform-tools`). A toolset never
widens access. Machine identity for autonomous agents is not supported yet. Writes through
agent-manager and model-manager are also made as the caller (`writesAsCaller: true`).

## Slack specifics

- Sign-in is a one-time account link: Swarmgeist posts a **Sign in to Giant Swarm** button, the
  person authenticates against the installation's Dex, and the callback requires the identity's
  verified email to equal the Slack profile email. The link is stored encrypted outside the pod.
- Every participant — initiator, collaborator in the thread, button clicker — must be linked
  before anything is dispatched. There is no service-account fallback.
- Slack itself does not let guest accounts use apps with the Agents feature. The gateway does not
  additionally check guest or foreign-workspace flags and serves any channel it is invited to, so
  Swarmgeist stays out of customer-facing channels until such a gate exists.

## Signing out

Three operations: per-device logout (`muster auth logout`, revokes that device's refresh-token
family), per-server disconnect (clears one downstream token and the cached capabilities), and sign
out everywhere (all downstream tokens and caches for the person). In Slack: ` /logout`.

## Observability

Every component ships Prometheus metrics with ServiceMonitors; the Muster chart ships the
*Muster / MCP Gateway* Grafana dashboard and alerts for servers that are genuinely broken
(`MusterMCPServerFailed`, `MusterMCPServerFlapping`; `Auth Required` is never alerted on).
agentgateway and the runtime export OTLP traces: one trace per turn, with the tool calls; klaus-
gateway emits a `turn_complete` record per Slack turn. The portal's MCP usage view reads the same
dispatch metrics.

## Sandbox

Actors run under gVisor on the worker pods; the runtime's `bash` tool executes in a per-session
directory (`/tmp/kagent/<session>/`) with `/skills` read-only; commands time out (30 s, Python
60 s). Egress from the worker pods is governed by Cilium network policies rendered by the
connectivity chart (the model provider, Muster, the snapshot store, the skill sources).
