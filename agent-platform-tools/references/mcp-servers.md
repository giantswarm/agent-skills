# MCP servers behind Muster

Public pages: https://docs.giantswarm.io/tutorials/agent-platform/managing-mcp-servers/,
https://docs.giantswarm.io/tutorials/agent-platform/connecting-custom-mcp-servers/,
https://docs.giantswarm.io/tutorials/agent-platform/multi-cluster-access/.

## The resource

```yaml
apiVersion: muster.giantswarm.io/v1alpha1
kind: MCPServer
metadata:
  name: remote-api-tools
  namespace: muster
spec:
  type: streamable-http        # stdio | streamable-http | sse
  url: "https://api.example.com/mcp"
  timeout: 30
  autoStart: true              # default false: defined, started when needed
  toolPrefix: ""               # default: the server name → x_<name>_<tool>
  description: Remote MCP server providing API tools.
```

- `stdio` (`command`, `args`) runs a child process **inside Muster** — for a local `muster serve`
  only; a Kubernetes Muster has no per-user process to start. On a cluster every server is its own
  service reached with `streamable-http` or `sse` (`url`, `headers`). Admission rejects a resource
  that mixes the two.
- `autoStart: true` for servers that should always be available (the per-cluster mcp-kubernetes);
  otherwise Muster loads the tool definitions when the server is first needed.
- Tools are discovered when the server starts, prefixed and registered live.

## Families

Several instances of the same server (one per management cluster) collapse to one tool set with a
required instance argument:

```yaml
spec:
  family:
    name: kubernetes
    instanceArg: management_cluster
```

All members must agree on `instanceArg` (otherwise Muster falls back to per-server prefixes and
logs a warning). The argument is always required, even for a single member; its value is the **full
server name** (`my-cluster-mcp-kubernetes`). mcp-prometheus and mcp-capi use their own `prometheus`
and `capi` families.

## The tool-group label

```yaml
metadata:
  labels:
    agent-platform.giantswarm.io/tool-group: infrastructure   # or agent-platform
```

Set by the charts that ship the platform's servers; the portal and the shipped presets read it. A
server without the label is a Registered server — do not set it on your own resources. Orientation,
not authorization.

## Authentication modes

Servers that trust the same Dex — token forwarding, with the audiences the downstream expects:

```yaml
spec:
  auth:
    type: oauth
    forwardToken: true
    requiredAudiences:
      - "dex-k8s-authenticator"
```

Muster collects `requiredAudiences` from every forwarding server at login and requests them from
Dex, so the forwarded token is accepted downstream (Kubernetes OIDC here).

Remote clusters with their own Dex — RFC 8693 token exchange:

```yaml
spec:
  auth:
    type: oauth
    tokenExchange:
      enabled: true
      dexTokenEndpoint: "https://dex.cluster-a.<base-domain>/token"
      connectorId: "central-dex"
      clientCredentialsSecretRef:
        name: cluster-a-token-exchange-credentials
```

Third-party servers:

- unauthenticated or static token: `headers: { Authorization: "Bearer <token>" }` (the token from a
  Secret through the deployment pipeline, never in Git);
- OAuth with RFC 9728 metadata: `auth.type: oauth` and Muster discovers the authorization server;
- OAuth without RFC 9728 (RFC 8414 at the issuer, e.g. Atlassian): `auth.authorizationServer:
  {issuer, scopes}` — mutually exclusive with `forwardToken` and token exchange; the server still
  reconciles to `Auth Required` until a person signs in.

The rule behind the modes: **who administers the backend's account system decides.** Platform-
administered backends derive authority from the person's identity per request (`forward`,
`exchange`); externally administered ones get Muster as an OAuth client toward their own
authorization server, with a one-time browser consent per person.

## States and checks

```bash
kubectl get mcpservers -n muster
muster auth status
```

Remote: `Connected`, `Auth Required`, `Connecting`, `Disconnected`, `Failed`; stdio: `Running`,
`Starting`, `Stopped`, `Failed`. `Auth Required` is the normal first-connect state of a protected
server and a permanent state for a server nobody is using — healthy. `Failed` means unreachable:
URL, DNS, network policy between Muster and the server. The resource-level state is
infrastructure; whether a given person is signed in and which tools they see is per user.
Alerts: `MusterMCPServerFailed`, `MusterMCPServerFlapping`.

## Where they are managed

Platform servers come from the platform charts (`agent-platform-mcps` renders the per-cluster
Infrastructure servers from one values file; the managers' charts render their own `MCPServer`).
An installation's own servers live in its management-clusters repository under
`extras/agent-platform/mcpservers/`; a person's servers come from the portal's registration wizard
(live-editable, no Git source). The portal's Servers page shows all three groups with sign-in.
