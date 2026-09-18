---
name: giantswarm-repository-ci-renovate
description: Use when a question is about a Giant Swarm repository's CI or Renovate — why it is not releasing or building, where its CircleCI pipeline, GitHub workflows, release workflow, Makefile or renovate.json5 come from, what Renovate's onboarding pull request means, how to change a generated file, or what devctl generates from the declaration. Carries the generation contract and the diagnosis order, never the generated content.
metadata:
  version: "1.3.0"
---

# CI and Renovate come from the declaration

A declared repository's CI is **generated**: the align-files workflow in https://github.com/giantswarm/github
runs `devctl gen` for every entry with the fields of its `gen` block and rewrites the generated files on
every run — `.circleci/config.yml` when `gen.ci.generate` is true, the `zz_generated.*` GitHub workflows,
`cliff.toml`, the root `Makefile` and `Makefile.gen.*.mk`, `renovate.json5`, `.nancy-ignore.generated`, the
pre-commit config when `gen.preCommit` is set. The pipeline's shape is derived from `gen.flavours`,
`gen.language` and whether a `Dockerfile` sits at the repository root — there is no per-repository
parameter block. So a CI question is a declaration question: the answer is a field, read from the schema
and changed through the entry. The entry, the set-up state and the recipes to find the manager's tools and
the schema are the `giantswarm-repository-setup` skill; lifecycle, `giantswarm-repository-lifecycle`.

## Fetch, in this order

1. **The declaration and the set-up state**: the manager's `get_repository` — the entry's `gen` block,
   whether CircleCI follows the repository, whether Renovate is configured and active, the latest release,
   the engine's checks with the last reconciler run.
2. **The generated files**, with the GitHub read tools in your toolset, from the repository's default
   branch: a generated file's header says so and names the devctl version and command that produced it —
   the file answers "which pipeline runs" and "which release workflow"; a file without the header is
   hand-maintained and the team's.
3. **What a field does**: its description in `.github/repositories.schema.json` of `giantswarm/github`
   (`gen.ci.generate`, `gen.ci.releaseWorkflow`, `gen.ci.appCatalog`, `gen.flavours`, `gen.language`,
   `gen.preCommit`, `choreReviewers`, …); what a flavour generates, `docs/flavours.md` in
   https://github.com/giantswarm/devctl. Never state from memory which flavours or fields exist.
4. **The runs**: the CircleCI project (`https://app.circleci.com/pipelines/github/giantswarm/<name>`) and
   the repository's Actions tab — the set-up state says whether CircleCI follows the repository at all.

## "Why is it not releasing" — top down, stop at the first miss

A release is a git tag that the CircleCI tag pipeline turns into images and charts; the tag comes from the
repository's release workflow.

- **Does the reconciler know the repository?** Undeclared (finding `undeclared-on-github`): nothing is
  generated and CircleCI is not followed by the automation — the fix is a declaration
  (`giantswarm-repository-setup`).
- **Is CircleCI following it, with setup workflows on?** A red step in the set-up state; *Align now*
  (`align_repository`) repairs it, in one of three modes: `align` — the repository has opted in
  (`align: true` in its entry) and the reconciler is dispatched now; `opt-in` — it is declared but has
  not: the commit opens the pull request that opts it in, the team reviews it from the ask in its
  channel, and the reconciler aligns the repository when it merges; `check` — it has no entry: only
  checked, from the team alone. The recipe is in `giantswarm-repository-setup`.
- **Which release workflow is generated?** `gen.ci.releaseWorkflow` — `auto-release` tags from the
  conventional commits on every push to `main` (when no tag appeared, the workflow's run in the Actions
  tab says what it computed from the commits); `legacy` releases through the create-release-pr /
  create-release / validate-changelog trio from a `main#release#patch`-style branch a person pushes — no
  push, no release. The effective default follows `gen.ci.generate`; the schema says how.
- **Does the tag pipeline have the jobs?** No image job — no root `Dockerfile`. A chart job on a
  repository without a chart — the `app` flavour is declared and should not be (a Go service without a
  chart is not an `app`). A chart in the wrong catalog — `gen.ci.appCatalog`.
- **Did the tag pipeline fail?** Then the CircleCI run is the answer, not the declaration.

## Renovate

Renovate runs on **every** repository of the org. A repository on generated CI (`gen.ci.generate: true`)
or with the `customer` flavour gets its `renovate.json5` from the generator, extending the giantswarm
presets (`lifecycle: deprecated` switches it to the security-only preset); every other repository keeps a
hand-maintained one. Renovate's pull requests are bot pull requests the team's sweep handles;
`choreReviewers` in the entry says whom Renovate asks to review. A repository **without** a Renovate
config gets Renovate's **onboarding pull request** ("Configure Renovate"): not an error, nothing to
suppress — on a declared repository the generated config supersedes it at the next align run; on an
unassigned repository it is the visible sign that nobody owns the repository, and the answer is a team
declaring it (`giantswarm-repository-lifecycle` finds those). `list_repositories` filters on the Renovate
state — `configured`, `missing`, `active`, `inactive`.

## Generated files are never hand-edited

A generated file is rewritten from devctl's template on the next align run: a hand edit vanishes or fights
the generator, and no other repository gets the improvement. Never suggest editing one. Instead:

- repository-specific configuration goes into the side files the generator leaves alone —
  `Makefile.custom.mk`, `.circleci/custom.yml`, `renovate-custom.json5`;
- a different shape (another flavour, the release workflow, the catalog, pre-commit flavours, `goGenerate`,
  `helmDocsRegen`) is a field of the entry: `update_repository` with the whole entry, the team reviews it,
  the next align run renders it;
- a change to what a generated file *does* for every repository is a change in `giantswarm/devctl`.

An entry without `gen.ci` keeps its hand-maintained CircleCI config while its workflows and Makefile may
still be generated — the file headers decide, not the repository's age.
