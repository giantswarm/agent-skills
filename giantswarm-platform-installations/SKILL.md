---
name: giantswarm-platform-installations
description: Use when a question is about the installations Giant Swarm operates and their platform capabilities — which installations exist, whether one has a capability such as the Agent Platform enabled, what state a capability is in and why, what a capability definition is and which inputs it takes, or whether an installation still matches its definition, in its repositories and on its running cluster (verify) — through giantswarm-platform-manager's tools behind Muster, acting as the person. Carries the vocabulary, how to read a state and a refusal, and the fetch recipes (get_info, list_installations, verify_capability, verify_installation); never a list of installations, capabilities, inputs or states.
metadata:
  version: "1.1.0"
---

# Installations and their platform capabilities

An **installation** is a Giant Swarm management cluster with everything it carries for its customer. The
platform manager knows it as an entry of the **registry** — the installations catalog, read as the person on
every call — with its two GitOps repositories, the configuration one and the management-clusters one. A
**platform capability** is a product configured on an installation, the Agent Platform for one, and each is
described by exactly one **capability definition**: a closed set of typed inputs that renders into files of
those repositories, Dex clients, generated secrets, customer actions and probes. The manager
(`giantswarm-platform-manager`) reads and renders as the person and writes only through pull requests in the
person's name. Behind Muster it is two registrations: `x_giantswarm-platform-manager_*` reads the record and
the actions, `x_giantswarm-platform-manager-live_*` reads the running cluster as the person. Enabling or
reconciling a capability is the `giantswarm-platform-capability-enablement` skill; an action's approval,
rollout and report, `giantswarm-platform-actions`; how `filter_tools`, `describe_tool` and `call_tool` work,
`agent-platform-tools`; what the Agent Platform itself is, `agent-platform-overview`.

## Fetch first, never recall

- **The tools**: `filter_tools {"pattern": "x_giantswarm-platform-manager*"}` finds both registrations; then
  `describe_tool` on the one you are about to call — every argument, mode and result field is in its schema,
  which changes faster than any skill. Never call a tool you have not described in this conversation.
- **`get_info` opens every conversation**: whose GitHub grant your calls carry (the caller), the hub
  installation, the registry it reads, the capability definitions with their input schemas, and what the
  manager is configured for — whether it can commit, whether the action record is readable, whether the
  live registration serves. Answer "which capabilities exist" and "what can I set" from it and only from it.
- **The installations and their states**: `list_installations` — every installation of the registry with
  its record (the facts the definitions take as `installation.*` inputs) and, per capability, the state, the
  inputs on record and the last action. Filter by name or customer; an unknown name is an error, not an
  empty list. `summary: true` answers the states and the last actions alone — the call for an overview. The
  result's `states` field names every state with its source, and its `unreadable` list names the
  installations whose repositories the person cannot read.
- **What is really configured**: two reads, one answer. `verify_capability` compares the installation's
  repositories with the definition — grouped into the definition's features, one mark each (*as defined*,
  *planned*, *differs by input*, *drifted*), every difference named by file, path and the input that drives
  it. `verify_installation`, on the live registration, checks the running cluster against the definition's
  probes, read through Muster's kubernetes tools as the person: an object they may not read is *not checked,
  forbidden for them*, never a failure of the installation. Each reports the other's dimensions as *not
  checked* there; present the two together.

## Reading a state

From the repositories a capability is *enabled* when its fileset is on record — whoever put it there, the
manager or the installation's people by hand — and *not enabled* when it is not. *Unknown* means the
repositories could not be read as the person (the installation is also under `unreadable`) — a permission
of the person's, not a fact about the installation. A running or finished action stands over the files'
state: *pending approval*, *rolling out*, *waiting for the customer*, *drifted*, *failed*
(`giantswarm-platform-actions` has them). Report the state the tool gives with its source; never infer
*enabled* from a file you saw elsewhere or from a cluster.

## Reading a refusal

- **`auth_required`** from Muster: the person is not signed in to that registration. The manager knows the
  person through the GitHub App its server is pinned to, so this is the person's own connection — hand them
  the sign-in link (`core_auth_login` for the server the refusal names, `giantswarm-platform-manager` or
  `giantswarm-platform-manager-live`) and stop. Do not retry, do not call another tool in its place, do not
  present the refusal as an empty result. A tool error saying it *needs a caller* is the same situation; a
  live read that answers with Muster's own sign-in means the person is not connected to that installation.
- **A 403 or 404 on the registry**: the manager's App is not installed on the registry repository, or the
  person cannot read it; the error names the requirement. Nothing to work around.
- **A missing hub, action namespace or live path** reported by `get_info` is the manager's configuration,
  not the person's; say so and name what `get_info` reports.
- **A commit refused at the gate** — the installation unreadable as the person, or without repositories on
  record — is recorded as an action in state *refused*, and the files' state stands. A prerequisite the
  definition names (a version the installation runs, the chart line its record selects, an API its cluster
  does not serve, a choice not on record) is a dry run's `commitRefused`, relayed as it stands.
- **A key the definition does not know** in an installation's files refuses the render, naming the key —
  an answer to relay, never a reason to drop the key or edit the file.

## Facts to keep straight

- The manager writes nothing to a cluster and nothing to a repository outside a pull request; a state
  changes when Flux has reconciled a merged pull request, never when a tool returns.
- The team that owns a capability owns it on every installation: there is no per-installation consent to
  collect before acting on one. What protects an installation is the pull request under its repository's
  review rules, one approval per action by a second person, a wave that stops at a red probe, and that
  nothing runs unattended.
- The record's facts — whether an installation is private, its chart line, its customer — are inputs the
  definition takes as `installation.*`; the person overrides one only knowingly.
- An installation the registry lists without repositories has nothing to read and nothing to render; the
  tools say so, and every wave skips it.
