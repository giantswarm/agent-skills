---
name: giantswarm-platform-installations
description: Use when a question is about the installations Giant Swarm operates and their platform capabilities — which installations exist, whether one has a capability such as the Agent Platform enabled, what state a capability is in and why, whether an installation has opted in to the platform manager and how its owners opt in, what a capability definition is and which inputs it takes, or whether an installation still matches its definition (verify) — through giantswarm-platform-manager's tools behind Muster, acting as the person. Carries the vocabulary, how to read a state and a refusal, and the fetch recipes (get_info, list_installations, verify_capability); never a list of installations, capabilities, inputs or states.
metadata:
  version: "1.0.0"
---

# Installations and their platform capabilities

An **installation** is a Giant Swarm management cluster with everything it carries for its customer. The
platform manager knows it as an entry of the **registry** — the installations catalog, read as the person on
every call — with its two GitOps repositories, the configuration one and the management-clusters one. A
**platform capability** is a product configured on an installation, the Agent Platform for one, and each is
described by exactly one **capability definition**: a closed set of typed inputs that renders into files of
those repositories, Dex clients, generated secrets, customer actions and probes. The manager
(`giantswarm-platform-manager`, its tools `x_giantswarm-platform-manager_*` behind Muster) reads and renders
as the person and writes only through pull requests in the person's name. Enabling or reconciling a
capability is the `giantswarm-platform-capability-enablement` skill; an action's approval, rollout and
report, `giantswarm-platform-actions`; how `filter_tools`, `describe_tool` and `call_tool` work,
`agent-platform-tools`; what the Agent Platform itself is, `agent-platform-overview`.

## Fetch first, never recall

- **The tools**: `filter_tools {"pattern": "x_giantswarm-platform-manager_*"}`, then `describe_tool` on the
  one you are about to call — every argument, mode and result field is in its schema, which changes faster
  than any skill. Never call a tool you have not described in this conversation.
- **`get_info` opens every conversation**: whose GitHub grant your calls carry (the caller), the hub
  installation, the registry it reads, the capability definitions with their input schemas, and what the
  manager is configured for — whether it can commit and whether the action record is readable. Answer
  "which capabilities exist" and "what can I set" from it and only from it.
- **The installations and their states**: `list_installations` — every installation of the registry with
  its record (the facts the definitions take as `installation.*` inputs), its opt-in and, per capability,
  the state, the inputs on record and the last action. Filter by name or customer; an unknown name is an
  error, not an empty list. The result's `states` field names every state with its source, and its
  `unreadable` list names the installations whose repositories the person cannot read.
- **What is really configured**: `verify_capability` for one installation and one capability — the
  repository comparison against the definition, the live comparison and the probes, grouped into features.
  It answers for any installation of the registry, opted in or not: it is the drift view owners read before
  they opt in, and the check people run after a rollout.

## Reading a state

A capability's state comes from the installation's repositories, and a running or finished action stands
over it (`giantswarm-platform-actions` has those states). From the repositories, the rule that is easy to
get wrong: ***not opted in* wins** — an installation without the declaration shows that state even when
its files say the capability is enabled. *Not enabled* and *enabled* are what the files say. *Unknown*
means the repositories could not be read as the person (the installation is also under `unreadable`) — a
permission of the person's, not a fact about the installation. Report the state the tool gives with its
source; never infer *enabled* from a file you saw elsewhere or from a cluster.

## The opt-in

The **installation opt-in** is a reviewed declaration in the installation's own management-clusters
repository — `list_installations` reports its path, whether it is present and what it says, per
installation. It is the owners' standing consent that the manager may write to the installation; it is
read on every call, never cached, and it is **the owners' pull request, never the manager's**: no tool opts
an installation in, and you never draft that change. Without it every tool stays read-only for that
installation — `list_installations` and `verify_capability` answer, every dry run renders and says that a
commit would be refused, `commit` refuses, and a wave lists the installation as *skipped: not opted in*.
There is no default-on: an installation joins when its owners say so and leaves when they withdraw the
declaration. Asked how to opt in, answer with the path and shape the tool reports (`howToOptIn`) and who
lands it: the installation's owners, through their own review.

## Reading a refusal

- **`auth_required`** from Muster: the person is not signed in to the manager's server. The manager knows
  the person through the GitHub App its server is pinned to, so this is the person's own connection —
  hand them the sign-in link (`core_auth_login` for the `giantswarm-platform-manager` server) and stop.
  Do not retry, do not call another tool in its place, do not present the refusal as an empty result. A
  tool error saying it *needs a caller* is the same situation.
- **A 403 or 404 on the registry**: the manager's App is not installed on the registry repository, or the
  person cannot read it; the error names the requirement. Nothing to work around.
- **A missing hub or action namespace** reported by `get_info` is the manager's configuration, not the
  person's; say so and name what `get_info` reports.
- ***Not opted in*** is not an error: it is the answer, with the path to the owners' declaration.
- **A key the definition does not know** in an installation's files refuses the render, naming the key —
  an answer to relay, never a reason to drop the key or edit the file.

## Facts to keep straight

- The manager writes nothing to a cluster and nothing to a repository outside a pull request; a state
  changes when Flux has reconciled a merged pull request, never when a tool returns.
- The record's facts — whether an installation is private, its chart line, its customer — are inputs the
  definition takes as `installation.*`; the person overrides one only knowingly.
- An installation the registry lists without repositories has nothing to read and nothing to render; the
  tools say so and it is skipped from every wave.
