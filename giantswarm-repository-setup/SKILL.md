---
name: giantswarm-repository-setup
description: Use when asked to create a Giant Swarm repository, to declare one or change its configuration in a team file of giantswarm/github, to read or explain a repository's set-up state (which step is red and what fixes it), or to align a repository now — through giantswarm-repo-manager's tools behind Muster, acting as the person. Carries the contract (the declaration is the desired state; validate → dry run → confirm → create; the two guards on machine approval) and the recipes to fetch the schema and the inventory live, never their contents.
metadata:
  version: "1.4.0"
---

# Repository set-up

A repository of the giantswarm org is an **entry in its team's file**, `repositories/team-<slug>.yaml` in
https://github.com/giantswarm/github. The entry is the desired state: the reconciler (a workflow in that
repository running the devctl engine) creates the repository from it and keeps its settings, branch
protection, CircleCI project, Renovate, CODEOWNERS, catalog entry and first release true to it. Everything
you do here is a change to that file, opened as a pull request **as the person** — never a hand change on
GitHub. Deprecating, archiving and transferring is the `giantswarm-repository-lifecycle` skill; what the
generated CI and Renovate do, `giantswarm-repository-ci-renovate`; how `filter_tools`, `describe_tool` and
`call_tool` work, `agent-platform-tools`.

## Fetch first, never recall

- **The tools**: `filter_tools {"pattern": "x_giantswarm-repo-manager_*"}`, then `describe_tool` for the
  one you are about to call — its description says whether it reads, writes as the person or only
  annotates the inventory, and what every argument means. Open every conversation with the manager's
  `get_info`: it proves whose GitHub grant your calls carry; a person without the grant connects GitHub
  in Muster before any write.
- **The schema**: `.github/repositories.schema.json` on the default branch of `giantswarm/github`, read
  with the GitHub read tools in your toolset (`filter_tools {"query": "read a file from a GitHub
  repository"}`). Every field, enum, default and its meaning is there and only there — answer "what can I
  set" from it. The team's file shows what its repositories already declare; the README of
  `giantswarm/github` explains the reconciler, the review rules and the per-team policy.
- **A repository's state**: the manager's `get_repository` — declaration, GitHub reality, CircleCI,
  Renovate, catalog, the engine's set-up checks with the last reconciler run, findings and the record's age.
  `refresh_repository` when the record's age matters. `list_repositories` for a team's, the person's
  (`scope: mine`) or the undeclared (`scope: unassigned`) repositories.
- **On the person's machine**: `devctl repo validate | create | status | reconcile` are the same engine
  as a CLI (`--help` per command).

## Creating a repository — the order is the point

1. **Gather the declaration**: at least `name`, `componentType`, `gen.language` and `gen.flavours`;
   `description` and `visibility` are desired state too. Take the choices from the schema, ask the person
   what you cannot infer. The template is derived from `componentType`, `gen.language` and
   `gen.flavours` — there is no template field. Two refusals to know before validating: a Go service
   without a Helm chart does not declare the `app` flavour (the chart pipeline would run against a chart
   that is not there), and `gen.language: node` is refused — the Node template is not available yet.
2. **`validate_repository`** with the team's slug and the entry (or `entries`). Its result *is* the dry
   run — exactly what `create_repository` would put in the pull request: each entry rendered with the
   schema's defaults, the implied template, whether the name is free on GitHub, and refusals as data in
   `entries[].problems`. Show the person the rendered entry and every problem; fix and validate again
   until it is clean. An error (not a problem) means validation could not run.
3. **Explain the guard notices before the person confirms.** A pull request that only adds valid
   entries, whose author is in the owning team or in `team-planeteers`, and adds **at most three**
   entries is *creation-only*: the machine approves it, it merges in about a minute, and the reconciler
   creates the repositories. `team-review` (author outside both teams) or `batch-review` (more than three
   entries) means the team reviews the pull request first. `names-unchecked` means the manager could
   not check the names on GitHub; the pull request's validation check will.
4. **Confirm, then `create_repository`** with `mode: "commit"` and a `reason` for the pull request body —
   the pull request opens as the person. `dryRun: true` returns the same as `validate_repository`;
   `mode: "apply"` is refused on every write tool: a repository without its declaration is drift.
5. **Answer with the pull request URL** and what happens next: creation-only merges by itself,
   otherwise the review the notice named; one sentence about the creation follows in the team's standup
   channel (`standupChannel`), with a sentence per failed step or finding of that run. A name that is
   taken (the repository exists, or redirects to a renamed one) is not a creation — it is a transfer or
   a plain addition with the team's review. The pull request merging is not the repository done — that
   is step 6.
6. **Follow it to readiness with `watch_repository`** (`describe_tool` for its arguments and answer;
   the pull request number is in `create_repository`'s own answer). Report each phase once as it
   completes — created, scaffolded, declared, merged, setUp, released — and call the repository ready
   only when the tool says `ready`; call it again while a phase is still pending. A failed phase names
   the phase and the reason (a red first release names the job).

Changing an existing repository's configuration is `update_repository` with the **whole entry** as it
should read afterwards (not a patch — `get_repository` has the current one), validated against the
schema and reviewed by the team.

## Set-up state: a red step and the knob that fixes it

`get_repository` carries the engine's checks — settings, permissions, protection and required checks,
CircleCI follow and setup workflows, Renovate, CODEOWNERS, description and visibility, lifecycle,
catalog, release — with the last reconciler run. Read a red step in this order:

- **The check names its fix.** What the engine cannot repair it reports with the fix; say that first.
- **Reality drifted from the declaration** (a hand change on GitHub, a lost CircleCI follow, a first
  release that never happened): `align_repository` — *Align now* — as the person. Its `mode` follows
  the repository's entry, one of three:
  - `align` — the entry says `align: true`: the reconciler is dispatched for that repository now.
  - `opt-in` — the repository is declared but has not opted in: nothing is dispatched. The commit opens
    the pull request that sets `align: true` in its entry (every other byte untouched, auto-merge armed)
    and delivers the ask with the Approve button to the team's channel — a member of the team other than
    the person approves — and the reconciler aligns the repository when the pull request merges. A
    repository created through the product carries the field from its creation.
  - `check` — the repository has **no entry**: it cannot opt in; the run needs `team` and only checks,
    reporting the drift — declare the repository.

  `dryRun: true` answers with the mode, the opt-in, the planned changes from the record's last check and
  a warning paragraph; for `opt-in` also the entry as it will read, the pull request and the ask (who
  approves, in which channel). Show it to the person before they confirm `mode: "commit"`. The standup
  channel hears nothing about an Align now itself (an opt-in that merges is a change like any other: the
  reconciler's own notice follows): the record shows `setup.pendingRun` until the run's result lands as
  `setup.lastRun` with its failed steps and findings; a run silent for 15 minutes leaves the finding
  `reconcile-run-missing`.
- **The declaration is wrong**: the fix is a field and lands through `update_repository`. The pipeline is
  derived from `gen.flavours`, `gen.language` and whether a `Dockerfile` sits at the repository root — no
  image job means no root Dockerfile, a chart job on a repository without a chart means the `app` flavour
  should go, the release workflow follows `gen.ci.releaseWorkflow`; the field descriptions in the schema
  say what each knob does, `giantswarm-repository-ci-renovate` has the diagnosis order.
- **No team**: an undeclared repository (finding `undeclared-on-github`) has no reconciler until a team
  declares it; a declared repository gone from GitHub (`repository-missing`) is an entry a person removes.

The nightly schedule walks the opted-in entries (`align: true`) of every team file and repairs their
drift; every other repository it only checks. The team's policy file `repository-setup/team-<slug>.yaml`
in `giantswarm/github` names the team's two channels and holds no opt-in: asks with an Approve button go
to `slackChannel`; notices — who created, added, transferred, archived or deprecated a repository, a
failed step, a finding of that person's run — to `standupChannel`. A run behind which nobody's change
stands (an Align now, the schedule) posts nothing.

## Rules of conduct

- Write only as the person and only after they confirmed the rendered change; reads and dry runs are free.
- Never suggest editing a generated file (`zz_generated.*`, the generated `.circleci/config.yml`,
  `Makefile.gen.*.mk`, a generated `renovate.json5`): the next align run overwrites it. Repository-specific
  configuration goes to `Makefile.custom.mk`, `.circleci/custom.yml` and `renovate-custom.json5`; a
  different shape is a field of the entry.
- Deletion is not something a declaration can say — `giantswarm-repository-lifecycle`.
