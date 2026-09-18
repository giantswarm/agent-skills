---
name: giantswarm-platform-actions
description: Use when a question is about an action of giantswarm-platform-manager — what happened after a commit, whether an enablement or a reconcile was approved, merged, rolled out or verified, why an installation is pending approval, rolling out, waiting for the customer, drifted or failed, who approves an action and where the ask lands, what a report says, or the history of actions on an installation — get_action and list_actions behind Muster, acting as the person. Carries the action's life, the approval's rules and how to read a record; never a list of actions, teams or channels.
metadata:
  version: "1.0.0"
---

# Actions: approval, rollout and report

An **action** is one commit of `enable_capability` or `reconcile_capability` by a person — or by you in a
person's session — over one installation or a set. It is a record on the hub installation that the manager
writes and the tools read: actor, capability, kind, installations in wave order, the inputs (never a secret
value), the pull requests with their state, the approval, the rollout per installation, the probes and the
result. `get_action` reads one by name; `list_actions` the history, newest first, filtered by installation
or capability; `list_installations` carries each installation's last action and takes its state from it
(`giantswarm-platform-installations`). Starting an action is the `giantswarm-platform-capability-enablement`
skill; `describe_tool` before the first call, as everywhere.

## The life of an action

1. **Pending approval.** The commit opened the pull requests in dependency order, each carrying the action,
   and asked for the **action approval**: one review in the channel of the team that owns the capability
   definition, posted by the platform's Slack app with the actor, the installations, the changed inputs and
   the pull request list, with an Approve and a Deny button; for a customer installation the customer's
   account engineers are informed as a group. A member of the owning team approves once, and the manager
   approves every pull request of the action as that member. The actor cannot approve their own action —
   four eyes, refused before it is asked. Deny records a reason and closes the pull requests. Approving on
   GitHub is equivalent. You approve nothing.
2. **Rolling out.** Approved and green, the pull requests merge as the actor, in order. The repositories'
   CI validates, Flux reconciles; the manager watches the releases and hurries nothing. A changed Dex
   client reaches Dex through Flux, never through a restart.
3. **Verified.** The probes run — `verify_capability`'s live pass — and the report goes into the same
   thread and onto the record: the pull requests, the rollout per installation, each probe's result, the
   open customer actions. The state becomes *enabled*, *waiting for the customer* or *failed* with the
   failing probe named. *Drifted* is a later verify finding the files or the cluster off the definition.

The opt-in is the owners' standing consent that the manager may act on the installation at all; the
approval is the review of one action. Neither replaces the other, and neither is yours to give.

## Reading a record

- **Where is it?** The state first, then the field for that stage — the pull requests (repository, number,
  URL, state) while pending; the approval (decision, who decided, reason, when) for the review; the rollout
  for the per-installation state and message; the probes and the result at the end. `describe_tool` names
  the fields; report what the record says, with its timestamps, not what you expect at this point.
- **Waiting for the customer** is not a failure: a customer action from the dry run is open — name it and
  its installation; the customer's people close it, and the next verify moves the state on.
- **Failed** names the pull request, installation or probe that failed in the result's message; relay it
  and stop. Trying again is a new dry run and a new confirmation of the person's, never yours.
- **A wave** is one action over N installations with one approval: read the rollout per installation and
  say which are done, which are pending, and which the dry run had skipped.
- **No action record readable** — `get_info` says the action reader is not configured — means the history
  is not available here; say so. The pull requests still exist under the person's name on GitHub.

## What you never do

Approve, deny, merge, re-request a review, poll for a state change, or restart an action. You read the
record when asked and relay it; the person and the owning team act.
