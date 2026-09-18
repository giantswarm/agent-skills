---
name: giantswarm-platform-capability-enablement
description: Use when asked to enable a platform capability on a Giant Swarm installation (the Agent Platform for one), to reconcile one after a definition or input change, to change an installation's inputs, to run a change over a set of installations as one wave, or to show what such a change would do — enable_capability and reconcile_capability of giantswarm-platform-manager behind Muster, acting as the person. Carries the contract (a dry run first, the person's confirmation, then one commit; what a dry run shows and how to present it; never a loop of your own) and the fetch recipes, never the inputs, files or installations themselves.
metadata:
  version: "1.0.0"
---

# Enabling and reconciling a capability

`enable_capability` turns a capability on for an installation that does not have it; `reconcile_capability`
re-renders one that has it — with the inputs on record or changed ones, for one installation or for a set,
where an empty set means every installation of the registry. Both render the **capability definition** from
the installation's record and the inputs, and both write only as a **commit**: pull requests in the
person's name to the installation's GitOps repositories, which start an **action** the owning team approves
(`giantswarm-platform-actions`). Nothing is applied to a cluster, no file is edited in place, and there is
no other write mode. Installations, states, the opt-in and how to read a refusal are the
`giantswarm-platform-installations` skill — its first section (`describe_tool` on every tool, `get_info`
first) applies here; `get_info` also says whether this manager can commit at all, and when it cannot, the
dry run is where you stop and say so.

## Dry run first, always

Every call starts as a dry run (`dryRun: true`; `describe_tool` names the argument). It renders and writes
nothing, as often as needed, for any installation of the registry — one that has not opted in is rendered
too, with `commitRefused` saying why a commit would be refused. Iterate here: change an input, render again,
until the plan is what the person wants. Present the result before anything else happens.

**Inputs** are the definition's typed choices, read from its schema in `get_info`. The set is closed: an
unknown key is refused, naming the key, and the choices the schema marks as the person's are not filled in
for them — a dry run that refuses for a missing choice is a question to ask the person, not a default to
pick. The record's `installation.*` facts are inputs too; override one only when the person says so. When
the plan is large, `content: false` returns paths and change kinds without file contents.

## Presenting a dry run

The person decides from your summary, so it carries everything the result carries, grouped as the result
groups it — read the fields from `describe_tool`, then say for each installation of the plan:

- **Refusals first**: `refused` (the definition would not render — an input, a policy, an installation the
  definition does not cover) and `commitRefused` (it renders, but a commit would be refused — the opt-in).
  Both are answers from the tool, relayed as they stand, never worked around.
- **The files per repository** with their change kind — create, update, unchanged — and the repository each
  lands in. An empty diff (every file unchanged) is a finding: the installation already matches; nothing
  to commit.
- **The pull requests**: one per repository across the set, in the order the manager will open them, each
  with its installations, changed files and generated secrets.
- **Secrets by name**: every generated secret with its kind and the files it lands in, and every supplied
  secret as the field the person fills. **Never a value**: values exist only inside the encrypted files of
  the pull request and appear in no dry run, log or message — if you ever see one, stop and report it.
- **The Dex clients** with their redirect URIs, **the customer actions** — what the customer's own people
  must do, per installation, and why — and **the probes** the action will run afterwards.
- **The order and the skipped**: over a set, the wave — the hub's own test installations, then the hub,
  then the customers — and every installation left out with its reason (*not opted in*, *unreadable*, *no
  repositories on record*). A skipped installation is never a target, however the set was named; say so.

Keep the shape of the tool's answer: do not summarise files into "some configuration changes", do not drop
a skipped installation, do not reorder the wave. When the dry run is long, give the counts per installation
first and the details on request.

## Confirm, then commit — once

Only after the person has seen the dry run and said yes do you call the same tool with `mode: "commit"` and
the same arguments. The manager checks the opt-in again at that moment and refuses an installation without
it; the result names the action and its pull requests, and everything from there — approval, merge, rollout,
probes, report — is the action's, read through `giantswarm-platform-actions`.

- One commit per confirmation. A refused or failed commit is reported, not retried; a changed plan is a new
  dry run and a new confirmation.
- You never loop on your own: no polling for the rollout, no re-running a reconcile because a state has not
  changed yet, no splitting a wave into single commits. A wave is one call over the set with one approval.
- You never approve, merge, push or comment around the action, and you never hand-write a file the
  definition renders — the pull request's content is the definition's output.
- `mode: "apply"` does not exist on this manager; do not offer it.
