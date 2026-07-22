---
name: k8s-debugging
description: Use when asked to debug Kubernetes clusters or workloads.
---

# Kubernetes debugging

Note: this collection gives hints that may not be common Kubernetes knowledge.
For CLI tools mentioned, use the MCP tool equivalents.

## Workloads

### Debug Pods

- **`Pending` and `Waiting` are different failure classes.** *Pending* = never
  scheduled onto a node (scheduler couldn't place it — resource exhaustion,
  `hostPort` conflict, taints). *Waiting* = scheduled, but the container can't
  start on that node (usually image pull / registry auth). Pending needs a
  cluster-side change; Waiting needs a pod-spec/registry fix.
- **Silent spec typos.** A misspelled key (`commnd:` instead of `command:`) is
  *silently ignored*, not rejected — the pod runs but not as intended. Guard with
  `kubectl apply --validate` and/or diff the deployed object
  (`kubectl get pod X -o yaml`) against your source.
- **`hostPort` caps schedulable replicas at the node count** — one pod per node
  per host port. This is a hard scheduling limit, and it's an easy-to-miss reason
  a Deployment won't scale past N pods.
- **Pod stuck `Terminating` can be caused by a finalizer + an admission webhook.**
  If a Validating/Mutating webhook targets `UPDATE` on pods (or a mutating webhook
  tries to change immutable fields during termination), the control plane can't
  remove the finalizer and the pod hangs. Check
  `kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations`.
- **Check the modern endpoints API**: `kubectl get endpointslices -l
  kubernetes.io/service-name=<svc>` rather than the older `endpoints`. A Service
  with N ready backends should expose N distinct IPs across its slices.
- Resource exhaustion is per-resource: the cluster may have spare CPU but no
  memory (or vice-versa) — check both `requests` and `limits` against node
  capacity, not just one.
- A failed pod does not necessarily indicate a problem/outage. It might be stale
  left-over from a previous version, not garbage-collected yet.

### Debug Services

- **A Service with no matching pods produces zero EndpointSlices** — an empty
  endpoint set is the first thing to check, and it points straight at a
  selector/label mismatch (exact-match only; `app: hostname` ≠ `app: hostnames`).
- **`port` vs `targetPort`.** Clients hit the Service `port`; pods listen on
  `targetPort`. When `targetPort` is a **name**, that exact name must exist in the
  container's `ports:` — a rename on one side breaks routing silently.
- **The cluster DNS domain is not guaranteed to be `cluster.local`** — it's set by
  kubelet's `--cluster-domain`. Troubleshooting guides assume `cluster.local`;
  confirm before trusting FQDNs.
- **`ndots:5` in the pod's `/etc/resolv.conf`** governs when the search path is
  applied. Short names resolve via the search list; a name with ≥5 dots is tried
  as absolute first. This is why cross-namespace short names fail — the search
  path only covers the pod's own namespace + cluster defaults, so from another
  namespace you must use `svc.ns.svc.cluster.local`.
- **kube-proxy silently depends on kernel modules.** iptables mode needs the
  `conntrack` module loaded, or connections fail without a clear error. IPVS mode
  needs `ip_vs`, `ip_vs_rr`, `ip_vs_wrr`, `ip_vs_sh`. Verify with `lsmod`.
- **Hairpin limitation**: a pod reaching *itself* through its Service ClusterIP is
  not reliable (CNI/kernel dependent). Use the pod IP or a headless Service for
  self-calls.
- **NetworkPolicy can block Service traffic while everything else looks correct.**
  A default-deny *ingress* policy on the backend pods drops traffic even with a
  perfect Service/endpoint setup. (Default-deny *egress* does not block inbound.)
- **No ClusterIP assigned (`<none>`)** can mean the service-cluster-IP range is
  exhausted — an API-server-side problem, not a manifest problem.
- Layered test ladder to localize the break: pod IP directly → Service ClusterIP →
  Service DNS name. Whichever hop first fails tells you if it's the app, the
  proxy/iptables layer, or DNS.

### Debug a StatefulSet

- **`podManagementPolicy` changes debugging assumptions.** With `OrderedReady`
  (default), pod N+1 won't be created until pod N is Running+Ready — so a single
  stuck early ordinal (e.g. `mysql-0`) blocks the *entire* set. With `Parallel`
  they come up together. A "stuck StatefulSet" is often just one wedged low
  ordinal.
- **Pods stuck `Terminating`/`Unknown` need the dedicated force-delete procedure**
  (Deleting StatefulSet Pods task), *not* an ordinary `kubectl delete` — deleting
  wrongly can violate the at-most-one-per-ordinal guarantee.
- List members via the recommended label `app.kubernetes.io/name=<app>`, then
  descend into per-pod and per-init-container debugging — StatefulSet issues
  usually originate a layer down.

### Determine the Reason for Pod Failure

- **Termination messages come from a file, not logs.** By default the kubelet
  reads `/dev/termination-log` (override with `terminationMessagePath`). The
  message surfaces in `status.containerStatuses[].lastState.terminated.message`,
  alongside `exitCode`, `finishedAt`, `containerID`.
- **`terminationMessagePolicy: FallbackToLogsOnError`** makes the kubelet use the
  *tail of the container logs* as the termination message — but **only** when the
  termination file is empty **and** the container exited non-zero. Great for apps
  that don't write a termination file.
- **Hard size limits:** 4096 bytes per container, and 12KiB total per pod split
  evenly across *all* containers (init + regular). Many containers ⇒ tiny
  per-container budget (12 containers ≈ 1024 bytes each). Messages beyond that are
  truncated.
- The message is only populated *after* the container terminates; you can't read
  it while it's running.
- `terminationMessagePath` cannot be changed after the pod is created.

### Debug Init Containers

- **The status string encodes progress:** `Init:N/M` = N of M init containers
  done; `Init:Error` = an init container exited non-zero; `Init:CrashLoopBackOff`
  = one is failing repeatedly. `PodInitializing`/`Running` means init already
  finished.
- **Init containers run strictly sequentially** — a failure in #1 blocks #2
  forever; the status never advances past `Init:0/2`.
- **Their status lives in a separate field**: `status.initContainerStatuses`
  (not `containerStatuses`), including its own `Restart Count`.
- **You must name the init container to get its logs:**
  `kubectl logs <pod> -c <init-container>`. Logs persist after init completes.
- **Liveness/readiness probes don't apply to init containers** — they simply run
  to completion or fail.
- Container logs _may_ be available via the MCP tool `x_kubernetes_logs`.

### Debug Running Pods

- **Ephemeral debug containers (`kubectl debug <pod> -it --image=...`)** are the
  answer for **distroless / shell-less images** where `kubectl exec` has nothing
  to run. The debug container is added to the live pod, shares its namespaces, and
  is auto-removed when the session ends — the original pod is not modified.
- **`--target=<container>`** shares the target container's process namespace so you
  can see/act on its PIDs. (Pod-wide, `spec.shareProcessNamespace: true` does the
  same for all containers — but that must be set at creation.)
- **`kubectl debug --copy-to=<newpod>`** clones the pod so you can *change the
  command* or *swap the image* on the copy — useful when the real container
  crashes immediately (change its entrypoint to keep it alive) without disturbing
  the original.
- **`kubectl debug node/<node> -it --image=...`** launches a privileged debug pod
  on a node with the host filesystem mounted at **`/host`** — for kubelet logs,
  node network config, disk/resource pressure.
- **Debug profiles** (`--profile=general|baseline|restricted|netadmin|sysadmin`)
  set the debug container's privileges appropriately — `netadmin`/`sysadmin` grab
  the capabilities needed for network / system-level tracing; `restricted` keeps
  it PSS-compliant.
- **`kubectl logs --previous` (`-p`)** reads the *last terminated* instance of a
  container — essential for a CrashLoopBackOff where the current instance's logs
  are empty or gone.
- Container logs _may_ be available via the MCP tool `x_kubernetes_logs`.

### Get a Shell to a Running Container

- **`--` is required** to separate kubectl's own flags from the in-container
  command; without it, flags meant for your command get eaten by kubectl.
- **`-i`/`--stdin` and `-t`/`--tty` are independent** — `-i` keeps STDIN open,
  `-t` allocates a pseudo-TTY. You need both for an interactive shell; a
  one-shot command (`kubectl exec pod -- env`) needs neither.
- **Multi-container pods**: without `-c`/`--container`, exec targets the pod's
  *first/default* container — a frequent source of "why am I in the wrong
  container" confusion.
- **`exec` cannot help a broken pod** — it needs a *running* container with the
  requested shell present. Crashed/Pending pods, or images with no `/bin/sh`, are
  out of reach → use ephemeral debug containers instead.
- Requires the `pods/exec` RBAC verb; security contexts / policies can still block
  what the shell may do.

## Clusters

### Control-plane failure model

- **Kubelets are autonomous.** If the API server is down, existing pods keep
  running and kube-proxy keeps routing Services — the data plane degrades
  gracefully. This is why "API server is down" ≠ "workloads are down", and why
  you can lose the control plane without an immediate outage.
- **Losing API-server backing storage (etcd) means kube-apiserver won't start**,
  but nodes keep serving existing pods. Recovery is an etcd-restore problem, not
  a workload problem.
- **Node-down taint/eviction timeline:** an unreachable node goes `NotReady`, gets
  `node.kubernetes.io/unreachable:NoSchedule` then `:NoExecute`, its `Ready`
  condition flips to `Unknown` with reason `NodeStatusUnknown` ("Kubelet stopped
  posting node status"), and **its pods are evicted after ~5 minutes** (the
  default `tolerationSeconds` for the unreachable/not-ready taints). A pod that
  "vanished" 5 min after a node blip is this, not a crash.
- Node conditions to read in `describe node`: `Ready`, `MemoryPressure`,
  `DiskPressure`, `PIDPressure`, `NetworkUnavailable` — pressure conditions drive
  eviction and scheduling independently of `Ready`.
- Control-plane / node log paths on non-systemd setups:
  `/var/log/kube-apiserver.log`, `/var/log/kube-scheduler.log`,
  `/var/log/kube-controller-manager.log`, `/var/log/kubelet.log`,
  `/var/log/kube-proxy.log`. On systemd, use `journalctl -u <unit>` instead.
- `kubectl cluster-info dump` dumps cluster-wide state (add `--output-directory`
  to write it out) — a one-shot snapshot for offline triage.

### crictl — debugging below the kubelet

- **crictl talks straight to the CRI socket, bypassing the API server and even the
  kubelet** — so it works when the kubelet is dead and can show pods/containers
  that never made it into `kubectl get pods` (orphans, failed syncs).
- **Set the endpoint explicitly** or it probes a list of known sockets and is slow:
  `--runtime-endpoint=unix:///run/containerd/containerd.sock` (or
  `CONTAINER_RUNTIME_ENDPOINT`, or `/etc/crictl.yaml`).
- **`crictl pods` (sandboxes) ≠ `crictl ps` (containers).** Every pod carries an
  extra **pause/sandbox** container — don't mistake it for an app container.
- crictl IDs and output format are **not interchangeable with kubectl** — different
  IDs, different columns; don't cross-reference by ID.
- `crictl images` shows **image digests (`sha256:…`)**, useful to confirm exactly
  which image a node pulled vs. what the tag claims.
- Core moves when kubelet/kubectl can't help: `crictl ps -a`,
  `crictl logs <ctr-id>`, `crictl inspect <id>`, `crictl exec -it <ctr-id> sh`,
  `crictl stats`.

### Debugging nodes with `kubectl debug node/`

- The debug pod shares the node's **host IPC / Network / PID namespaces** but is
  **unprivileged by default** (legacy profile) — so `chroot /host` **fails** until
  you raise privileges with **`--profile=sysadmin`**.
- The node root filesystem is mounted at **`/host`** — read kubelet/containerd logs
  at `/host/var/log/...`, kernel log at `/host/var/log/kern.log`.
- **This uses the API to schedule a pod, so it needs the node's kubelet to be
  working** — it does *not* work on a genuinely down/unreachable node (that's what
  SSH or console access is for). Its advantage over SSH is it needs no node-level
  network path or SSH creds, only `pods` create + `pods/exec` RBAC.
- **Gotcha with a containerized kubelet:** if the kubelet runs in its own mount
  namespace, `/host` reflects *that* namespace's root, not the true node root.
- Auto-named `node-debugger-<node>-xxxxx`; clean up with
  `kubectl delete pod <name> --now`.

### Resource metrics pipeline / `kubectl top`

- **metrics-server is for autoscaling, not monitoring.** It keeps only a short
  in-memory window (no history, no persistence, lost on restart), so never treat
  `kubectl top` numbers as an observability record — that's Prometheus's job.
- **`kubectl top` is a client of the Metrics API (`metrics.k8s.io`)** served via the
  aggregation layer. Empty/`error: Metrics API not available` almost always means:
  metrics-server not installed, its `APIService` not registered, or it can't reach
  the kubelet `/metrics/resource` endpoint (TLS). New pods also show nothing for
  the first ~1–2 min.
- **CPU is a rate over a window** (from the cumulative kernel counter, ~30s window
  exposed in the `window` field), **not** an instantaneous sample — so it lags
  spikes. **Memory is working set at the instant of collection**, and *includes
  unreclaimable page cache* — which is why it can read higher than an app's heap.
- cAdvisor gets these from **cgroups**; VM/non-cgroup runtimes must implement CRI
  container stats or `kubectl top` for their pods is blank.

### Node Problem Detector

- **The temporary/permanent split maps to Event vs NodeCondition.** Transient
  issues → Events (don't affect scheduling); permanent issues → **custom Node
  Conditions** that *do* influence the scheduler. NPD *surfaces* problems as node
  state — it does **not** remediate or reboot.
- It only detects **infra-level** problems (kernel oops, OOM in dmesg, runtime/
  kubelet unresponsive via HealthChecker). It does **not** watch app health
  (that's probes), network reachability, scheduler, or etcd.
- NPD needs **privileged mode** to read kernel logs (`kmsg`/`journald`/`filelog`) —
  it can't run under restricted PSS.
- **Distro log-path dependency:** the `hostPath` for system logs (`/var/log/...`)
  varies by distro; get it wrong and NPD silently detects nothing.
- Vendor/custom kernel log formats and bespoke hardware checks need **code-level
  extension** (a new log watcher, or a CustomPluginMonitor script using the
  exit-code protocol) — not just config.

### Audit logs — the forensics source of truth

- **Audit is off until you pass `--audit-log-path`** (or a webhook config) to the
  apiserver, and for a static-pod control plane the log dir must be a mounted
  `hostPath` or entries are lost with the pod.
- **Four stages** per request: `RequestReceived`, `ResponseStarted` (long-running/
  watch only), `ResponseComplete`, `Panic`. One watch can emit several — trim with
  `omitStages: ["RequestReceived"]`.
- **Four levels:** `None`, `Metadata` (who/when/what/verb, no bodies), `Request`
  (+ request body), `RequestResponse` (+ response body). Use `RequestResponse` on
  secrets/RBAC, `Metadata` on chatty resources, `None` to drop leader-election
  configmaps and `/healthz`,`/metrics` noise.
- **Policy is first-match-wins, top to bottom** — specific rules MUST precede
  general ones, or the general rule swallows them. A policy with zero rules is
  rejected.
- **"Who deleted / changed X?"** → filter on `verb: ["delete","patch"]` at
  `RequestResponse`, then read the `user` and `sourceIPs` fields. **PATCH bodies
  are JSON-patch arrays** (`[{"op":"remove",...}]`), not normal object shapes — a
  removal can hide inside a patch, so don't only look for `delete`.
- **Webhook backend defaults to `batch` and can silently drop events on buffer
  overflow.** `blocking-strict` guarantees capture but makes audit failures fail
  the API request — pick deliberately.
- `resourceNames` matches exact names only, and **subresources need their own
  rules** (`pods/log`, `pods/exec`, `pods/status` aren't covered by a `pods` rule)
  — easy to under-audit exec/attach access to secrets-bearing pods.

Adapted from the Kubernetes documentation (https://kubernetes.io/docs/),
© The Kubernetes Authors, licensed under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Modified.
