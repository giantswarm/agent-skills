# Kubernetes troubleshooting

A non-invasive, `kubectl`-first approach to triaging a misbehaving workload.
Everything here is read-only unless explicitly marked as a mutating action.
Always be explicit about which cluster/context you target — pass `--context`
rather than relying on ambient current-context, especially in multi-cluster
environments.

## Read-only triage sequence

1. **Locate the object and its status.**
   ```
   kubectl get pods -n <ns> -o wide
   kubectl get deploy,rs,sts,ds -n <ns>
   ```
   Look at `READY`, `STATUS`, `RESTARTS`, and age.

2. **Describe it — read the events.**
   ```
   kubectl describe pod <pod> -n <ns>
   ```
   The `Events` section at the bottom is usually the fastest clue (scheduling
   failures, image pulls, probe failures, OOM kills).

3. **Read logs, including the previous container if it restarted.**
   ```
   kubectl logs <pod> -n <ns> [-c <container>]
   kubectl logs <pod> -n <ns> -c <container> --previous
   ```

4. **Check recent cluster events chronologically.**
   ```
   kubectl get events -n <ns> --sort-by=.lastTimestamp
   ```

5. **Check resource pressure and scheduling.**
   ```
   kubectl top pods -n <ns>        # needs metrics-server-style backend
   kubectl top nodes
   kubectl describe node <node>    # allocatable vs requests, conditions, taints
   ```

6. **Check config and wiring (read-only).**
   ```
   kubectl get svc,endpoints -n <ns>
   kubectl get ingress,networkpolicy -n <ns>
   kubectl get configmap,secret -n <ns>   # names only — do not dump secret values
   ```

## Common failure modes

| Symptom (`STATUS` / event) | Likely cause | First checks |
|---|---|---|
| `ImagePullBackOff` / `ErrImagePull` | Bad image ref, missing/invalid pull secret, registry unreachable | `describe pod` event; verify image tag exists and pull secret is present |
| `CrashLoopBackOff` | App exits on start; bad config; missing dependency | `logs --previous`; check env/config/mounts; check the dependency is reachable |
| `CreateContainerConfigError` / `CreateContainerError` | Missing/invalid ConfigMap/Secret key, or invalid value | `describe pod`; verify referenced keys exist and values are well-formed |
| `Pending` (unschedulable) | Insufficient resources, taints/affinity, no matching node | `describe pod` scheduling events; `describe node`; requests vs allocatable |
| `OOMKilled` (in restart reason) | Memory limit too low or a leak | container memory limit vs actual usage; memory metrics over time |
| Readiness failing / not `Ready` | Readiness probe misconfigured or dependency not up | probe config; hit the readiness endpoint from inside the cluster; dependency health |
| Liveness restarts | Liveness probe too aggressive; slow start | probe thresholds and `initialDelaySeconds`; startup time |
| Service has no endpoints | Selector/label mismatch; pods not `Ready` | compare `svc` selector to pod labels; check pod readiness |
| Connection refused/timeouts between pods | NetworkPolicy, DNS, or wrong port | `networkpolicy` in ns; DNS resolution; `svc`/`endpoints` ports |
| TLS/cert errors | Expired/mismatched cert, wrong CA | certificate validity and SANs; issuer/CA config |

## Multi-cluster / Cluster API note

On platforms that separate a **control-plane/management cluster** from
**workload clusters**, be deliberate about which you are acting on. Cluster
lifecycle is often managed declaratively (e.g. via the Cluster API `Cluster` and
related resources) from the management cluster, while application workloads live
in the workload clusters. Investigate at the right layer:

- Application/workload symptom → look in the workload cluster.
- Cluster provisioning, scaling, or upgrade symptom → look at the Cluster API
  resources and controllers in the management cluster.

Match your `--context` to the layer you intend to inspect.

## Safety reminders

- Everything above is read-only. Restarting, scaling, deleting, editing, or
  cordoning are **mutating** actions — confirm intent, state the expected effect,
  and know the rollback before running them.
- Never print or paste secret values. Reference secrets by name only.
- Do not disable a security control (NetworkPolicy, admission policy, RBAC) to
  clear a symptom without owner approval.
