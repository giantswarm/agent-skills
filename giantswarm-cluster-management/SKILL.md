---
name: giantswarm-cluster-management
description: Use when asked to list, create or delete a workload cluster on a Giant Swarm installation, to show which releases a new cluster can run, to add or remove a cluster's GPU node pools, or to explain why such a change was refused — cluster-manager's tools behind Muster, acting as the person, applied to the installation or as a pull request in the person's name. Carries the contract (get_info first, a dry run, the person's confirmation, then one call; apply or commit; every refusal with its way out; a removal's live step) and the fetch recipes, never the tools' schemas, releases or clusters themselves.
metadata:
  version: "1.0.0"
---

# Creating and deleting workload clusters

A **workload cluster** on a Giant Swarm installation is a Flux HelmRelease of the provider's **release chart**
(`release-<provider>` at the release's version) in the organization's namespace `org-<organization>`, with its
OCIRepository and a values ConfigMap. cluster-manager composes those objects and writes them as the person, in
one of two **write modes**: **apply** lands them on the installation with the person's identity (Kubernetes RBAC
decides, the audit log names them); **commit** opens a pull request as the person in the git repository the
organization is reconciled from, in the layout that repository already uses, and the merge lands it. Behind
Muster it is one server, `cluster-manager`, and every tool is `x_cluster-manager_*`; how `filter_tools`,
`describe_tool` and `call_tool` work is the `agent-platform-tools` skill.

## Fetch first, never recall

- **The tools**: `filter_tools {"pattern": "x_cluster-manager_*"}` finds them; then `describe_tool` on the one
  you are about to call. Every argument, default, mode, name rule and result field is in its schema and
  description, which change faster than any skill. Never call a tool you have not described in this
  conversation, and never fill in an argument the person did not give and the schema does not default.
- **`get_info` opens every conversation**: the server's version, the write modes this installation offers
  (`modes`: commit only where cluster-manager is registered with its GitHub App), its tools, and whether the
  installation serves the Cluster API at all. Where commit is not offered, say so and offer apply; where the
  Cluster API is absent, there are no clusters to list or name here, and you say that instead of calling on.
- **The reads**: `list_clusters` for the clusters and their readiness, `list_releases` for what a new cluster
  can run (newest first per provider; `offered` and its `note` say whether `create_cluster` takes a release and
  why not), `list_node_pools` for a cluster's pools. Answer from them, as they stand, never from memory.

## The loop: dry run, confirmation, one call

Every write — `create_cluster`, `delete_cluster`, `create_node_pool`, `delete_node_pool` — goes the same way:

1. The tool with `dryRun: true` and the mode you mean to use. It writes nothing, as often as needed: a changed
   name, release or value is a new dry run.
2. The dry run shown to the person, in the tool's own shape: the objects (apply) or the repository, branch,
   directory and files (commit); for a deletion everything that goes with it; any refusal first.
3. The person's explicit yes to that dry run. Silence, a question or "looks fine, but…" is not a yes.
4. The same call once more, same arguments, without `dryRun`. One call per confirmation: a refused or failed
   call is reported with what it said, not retried; a changed plan is a new dry run and a new confirmation.

You never loop on your own: no polling a cluster until it is ready, no re-running a write because a state has
not changed yet. Readiness is a read the person asks for, or the next step the answer names.

## Apply or commit

- **Commit is preferred where the organization is reconciled from git** and `get_info` offers it: the cluster
  then lives where the organization's other clusters live, and the pull request is the person's, reviewed like
  any other change. Hand the person the pull request's link from the answer; the cluster exists once it is
  merged and Flux has reconciled it.
- **Apply** creates a cluster that git does not know about. Say so when the organization is reconciled from
  git and the person still asks for apply. Apply never patches or deletes an object a Flux Kustomization owns.
- A re-run of `create_cluster` with the same arguments changes nothing; its dry run shows the difference to
  what is there.

## Refusals and their way out

A refusal is the tool's answer, relayed with its reason and everything it names, never worked around — no
other tool, no hand-written manifest, no direct pull request. Then say the way out:

| Refused because | The way out |
|---|---|
| The name breaks the name rule or a cluster on the installation uses it | Another name, checked again by a dry run |
| The release is not active, unknown, or its release chart is not published | A release `list_releases` offers |
| The organization's namespace carries no installation values | Not the person's to fix: the installation's owners provide them; name the organization |
| The values do not match the release chart's schema | Each violation by its path, fixed in the values and dry-run again |
| A given value contradicts a composed one (name, organization, description, release, cloud identity) | Set it through its own argument, not in the values |
| Commit: the organization is not reconciled from git, or its repository lacks the organization's directory | Apply, saying that git will not know the cluster |
| Apply: the object is in a Flux Kustomization's inventory | Change it in git: commit mode, or the repository's own process |
| Delete: a cluster cluster-manager did not create | Delete it the way it was made; it is not this tool's |
| Delete: the installation's own cluster | None: it is never deleted from here |
| Delete: helm-controller has not reconciled the release since its last write | Wait for the reconcile, then the same dry run again |
| `auth_required` from Muster, or commit lacks the person's GitHub consent | The sign-in link from `core_auth_login` for `cluster-manager`, and nothing else until the person is back |

A refusal the table does not name is relayed as it stands, with what the tool says to do.

## Deleting a cluster

- **The dry run is the decision.** It lists what goes with the cluster — its GPU node pools, the GPU operator
  release, the serving slice, the models served on it — or the refusal. Show all of it: a person deleting a
  cluster that serves models must see the models by name before saying yes. A cluster with pools or serving
  is not refused; everything listed goes with it.
- **Apply** removes the cluster as the person, without waiting for the uninstall. The answer's `nextStep`
  says what remains: a second call with the same arguments, once `list_clusters` no longer lists the cluster,
  removes what the uninstall left. That second call is part of the deletion the person confirmed; say so
  when you run it, and run it only when the read shows the cluster gone.
- **Commit** opens the removal pull request. Where the organization's Flux prunes, the merge deletes the
  cluster. Where it does not, the answer's live steps name the one call that finishes it after the merge
  (`delete_cluster` in apply mode, which deletes only what has left git). Tell the person before they merge;
  after the merge, offer the live step, show its dry run, and run it only on their yes.

## GPU node pools

`create_node_pool` and `delete_node_pool` follow the same loop and the same modes; their descriptions carry
what a pool composes, what goes with the last one and how a pool that cannot launch is explained. A pool of a
cluster created by commit goes into that cluster's directory in commit mode as well.
