# A GitOps agent: `HelmRelease` of the `agent` chart

On a Giant Swarm installation this lives in the installation's management-clusters repository under
`management-clusters/<mc>/extras/agent-platform/agents/<name>.yaml`, listed in that directory's
`kustomization.yaml` next to the shared `OCIRepository`. Flux applies it; the portal shows the Git
source and treats the agent as read-only; agent-manager reports it as `managed: gitops`.

The shared chart source (once per namespace):

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: agent
  namespace: flux-giantswarm
spec:
  interval: 10m
  url: oci://gsoci.azurecr.io/charts/giantswarm/agent
  ref:
    semver: ">=1.2.0 <2.0.0"
  provider: generic
```

The agent:

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: example-agent
  namespace: flux-giantswarm
spec:
  releaseName: example-agent          # the technical name; agent.name defaults to it
  chartRef:
    kind: OCIRepository
    name: agent
    namespace: flux-giantswarm
  interval: 10m
  targetNamespace: kagent             # next to the ModelConfigs and the Harness
  timeout: 10m
  install:
    remediation:
      retries: 10
      remediateLastFailure: false
  upgrade:
    remediation:
      retries: 10
      remediateLastFailure: false
  driftDetection:
    mode: enabled                     # enforce the rendered objects against out-of-band writes
  values:
    toolset:
      - preset:read-only
    agent:
      displayName: "Example Agent"
      description: "What this agent is for, one sentence."
      iconUrl: https://avatars.<base domain>/v1/example-agent.png
      systemMessage: |
        You are …

        <the Muster meta-tool paragraph from system-prompt.md>
    modelConfig:
      name: default-model-config
    skills:
      - name: agent-platform-overview
        path: agent-platform-overview
        git:
          url: https://github.com/giantswarm/agent-skills
          commit: <full 40-hex commit>
    # Only for skills from a private repository; the Secret (key `token`) is the
    # installation's, SOPS-encrypted next to the other platform secrets.
    # skillsGitAuthSecretRef:
    #   name: kagent-skills-token
```

Checks before the pull request: `kustomize build` the directory; `helm template` the values against
the chart (`helm template x oci://gsoci.azurecr.io/charts/giantswarm/agent --version <v> -f values.yaml`)
— the chart fails the render on an unpinned skill, an empty toolset or a credential on a plain
`http` source. After the merge: `flux reconcile source oci agent -n flux-giantswarm`,
`flux reconcile helmrelease <name> -n flux-giantswarm`, then the template's `Ready`.

Changing a GitOps agent is a commit; the same values through `update_agent` are refused (`managed:
gitops`) unless forced, and a forced write is reverted by Flux at the next reconcile.
