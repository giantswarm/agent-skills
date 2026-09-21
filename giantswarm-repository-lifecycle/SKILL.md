---
name: giantswarm-repository-lifecycle
description: Use when asked to deprecate, archive, delete, hand over or transfer a Giant Swarm repository, to adopt into a team one that exists on GitHub and no team file declares — alone or together with the lifecycle that ends it —, to say who owns one, whose approval a team-file change needs and where the ask lands, or to find repositories that look abandoned or unowned (unassigned, inactive, archived on GitHub, findings) — through giantswarm-repo-manager's tools behind Muster, acting as the person.
metadata:
  version: "1.5.0"
---

# Repository lifecycle and ownership

Ownership and lifecycle are properties of the repository's entry in its team's file
(`repositories/team-<slug>.yaml` in https://github.com/giantswarm/github): the owner is the file the entry
lives in, the stage is `lifecycle`. Every change here is a team-file pull request opened as the person and
approved by the team it concerns; nothing is done on GitHub by hand. Creating and configuring a repository,
reading its set-up state and the entry to propose when adopting one is the `giantswarm-repository-setup`
skill — it also has the recipes to find the manager's tools and to read the schema; Renovate and CI,
`giantswarm-repository-ci-renovate`.

## What each change does

`describe_tool` on the tool before the first call; the contract that is easy to get wrong:

- **Deprecate** — `set_lifecycle` with `lifecycle: deprecated`: the component is being phased out. A
  generated Renovate config drops to security-only updates, the portal catalog flags it, the team digests
  skip it. The repository keeps working, building, releasing and taking pull requests.
- **Archive** — `set_lifecycle` with `lifecycle: archived`: the work is over. The reconciler archives the
  repository on GitHub (read-only) and unfollows its CircleCI project. **The entry stays in the team file as
  the record** — nothing removes it, and the repository is never recreated. Un-archiving is not something
  the automation does; ask the person what they actually need.
- **Delete** — `set_lifecycle` with `lifecycle: deleted` **and `confirm`, the repository's name as the person
  typed it** (with or without the org; the tool refuses the deletion without it, and you never fill it in for
  them — ask for the name and pass it as given). The reconciler unfollows the repository's CircleCI project and
  deletes the repository on GitHub — code, issues, pull requests, releases and packages with it; an organization
  owner can restore it on GitHub for 90 days. **The entry stays in the team file as the record of the deletion.**
  A repository that is already gone from GitHub (finding `repository-missing`) is recorded the same way. Say
  what is lost before the dry run; an archive is the reversible alternative when the person hesitates.
- **Transfer** — `transfer_repository` with the receiving team's slug: one pull request that moves the
  entry from the giving team's file into the receiving team's and names both teams. After the merge the
  reconciler re-applies permissions, CODEOWNERS and the catalog mapping for the new owner. A repository
  that exists on GitHub but is declared by nobody is not transferred — it is adopted (below).
- **Adopt** — `adopt_repository` with the adopting team's slug, the `entry` as it goes into the team file
  and the person's `reason`: a repository that exists on GitHub and no team file declares (the inventory's
  `unassigned` scope) gets its declaration in that team's file, in a pull request the team reviews — an
  existing name is a plain addition, never machine-approved; the entry to propose and the `align`
  question are in `giantswarm-repository-setup`. **Adopt and end** — `lifecycle: deprecated` or `archived`
  in that entry: the one pull request declares the repository and ends its life, and the reconciler run of
  the merge applies the lifecycle; the manager writes `align: true` beside it, as `set_lifecycle` does, and
  the plan and the ask say so. Say what the lifecycle does (above) before the dry run, as for a declared
  repository. `lifecycle: deleted` is refused there: adopt first, then `set_lifecycle` with the name typed.
  Refused before any write when the name is free on GitHub (a creation) or declared already (the refusal
  names the team and the tool to use).
- **Back to production** — `update_repository` with the whole entry and `lifecycle` at its default.

`reason` goes into the pull request body and the ask — always pass the person's why. An entry without
`align: true` gets it in the same pull request: `set_lifecycle` writes it beside `lifecycle`, and the ask says
so — from the merge on the reconciler aligns the repository instead of only checking it
(`giantswarm-repository-setup`). `dryRun: true` renders the change and writes nothing; `mode: "commit"` opens
the pull request as the person; `mode: "apply"` is refused on every write tool.

## Whose review, and where the ask lands

Only a *creation-only* pull request is machine-approved (`giantswarm-repository-setup`). Every lifecycle and
ownership change is a person's decision, reviewed through `CODEOWNERS`:

- deprecate, archive, a configuration change: the **owning team** — the ask goes to its Slack channel;
- transfer: the **receiving team** approves in its channel; the giving team gets a notice in its standup
  channel;
- adopt, with or without a lifecycle in the entry: the **adopting team** — the ask goes to its channel and a
  member other than the person approves; the pull request carries auto-merge and lands on that approval.

Both channels are in `repository-setup/team-<slug>.yaml` of `giantswarm/github` — asks with an Approve
button go to `slackChannel`, notices to `standupChannel`; read that file when the person asks where a
message went. A team without a file gets no message — the pull request is then reviewed on GitHub alone,
and the person tells the team. An undelivered ask is named in the tool's result; approving on GitHub is
equivalent. A member approves with the Approve button of the
Slack ask or with an approving review on GitHub; `approve_change` with the pull request number in
`giantswarm/github` does the same from a chat, after the manager has confirmed on GitHub that the caller is a
member of the team the change belongs to — a non-member is refused, and you never approve, merge or push
around this review yourself.

## Abandoned or unowned repositories

The inventory carries the facts, not a verdict: each row of `list_repositories` names the team, the lifecycle,
whether GitHub has the repository archived, the last commit by a person, the Renovate state, the finding kinds
and the set-up state; `get_repository` has the full record. `describe_tool` names the filters (`scope`, `team`,
`search`, `renovate`, `visibility`, `fork`, `lifecycle` — `active`, `deprecated`, `archived`, where archived on
GitHub counts as archived, `deleted` — `archived` (archived or declared deleted), `inactiveDays`, `finding`). Read the facts to the person and let them
judge: `inactiveDays` for repositories nobody committed to in a while, `renovate: inactive` for a configured but
silent Renovate, `finding` for a specific gap. Scope the question: `mine` for the person's teams, `team` for one
team, `unassigned` for repositories on GitHub without a declaration — those have no owner, no reconciler and no
channel, and Renovate's onboarding pull requests on them are the visible sign (`giantswarm-repository-ci-renovate`).
The way on for one of them is `adopt_repository`: into the team whose work it is, or with the lifecycle that
ends it.

There is no note to leave on a record. A repository that stays as it is needs nothing; any other outcome is a
lifecycle change, a transfer or an adoption above, with the review it needs, and takes effect through its pull
request.
