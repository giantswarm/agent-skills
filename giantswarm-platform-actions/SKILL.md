---
name: giantswarm-platform-actions
description: Use when a question is about an action of giantswarm-platform-manager — what happened after a commit, whether an enablement or a reconcile was approved, merged, rolled out or verified, why an installation is pending approval, rolling out, waiting for the customer, drifted or failed, why an action reads refused, denied or removed, who approves an action and where the ask lands, who merges and who watches the rollout, what a report says, or the history of actions on an installation — get_action, list_actions, merge_action and watch_action behind Muster, acting as the person. Carries the action's life, the approval's rules and how to read a record; never a list of actions, teams or channels.
metadata:
  version: "1.3.0"
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
   definition — a line saying who asks to enable or reconcile which capability on which installations, the
   pull requests as its links, an Approve and a Deny button; a notice without buttons goes to a second
   channel when a customer installation is a target, naming the account engineer the catalog records for
   it. A member of the owning team approves once, and the
   manager submits an approving review on every pull request of the action as that member. The actor cannot
   approve their own action — four eyes, refused before it is asked. Deny records a reason, closes the pull
   requests and ends the action as *denied*; the actor may withdraw their own that way. The buttons are
   `approve_action` and `deny_action`, called as the clicking member; you press neither.
2. **Rolling out.** The merge is the actor's call, `merge_action`: each pull request once its checks are
   green, in dependency order; called before the approval it answers what the action waits for, posts the
   review when none is up and re-posts it when the gateway no longer holds it. The repositories' CI validates,
   Flux reconciles. The watch is a call too — `watch_action`, by anyone signed in: it reads the Flux objects
   the definition names on the installation rolling out, as the person calling, and answers the picture as it
   is; nothing is waited for or hurried. A changed Dex client reaches Dex through Flux, never through a
   restart.
3. **Verified.** Once every object is Ready, the same watch runs the definition's probes — the live
   dimensions as the person, the HTTP probes direct — and the report goes into the review's thread and onto
   the record: the pull requests, the rollout per object, each probe's result, the open customer actions.
   The stage becomes *enabled*, *waiting for the customer* or *failed* with the failing probe named.
   *Drifted* is a later verify finding the files (`verify_capability`) or the cluster (`verify_installation`)
   off the definition.

The record follows GitHub on every read, as the person reading, at most once a minute per action: a pull
request merged outside the manager is recorded *merged* with who merged it, and the action rolls out as
after `merge_action` with its approval recorded as *merged without approval by* that person; one closed
unmerged fails the action. An approving review on GitHub alone decides nothing: the approval is the
review's buttons, or the merge.

## Reading a record

- **Where is it?** The state first, then the field for that stage — the pull requests (repository, number,
  URL, state) while pending; the approval (decision, who decided, reason, when) for the review; the rollout
  for the per-installation state and message; the probes and the result at the end. `describe_tool` names
  the fields; report what the record says, with its timestamps, not what you expect at this point.
- **Refused** is the gate's answer before any write — the installation unreadable as the person, or without
  repositories on record; nothing was opened. **Denied** is a member's decision with its reason. **Removed**
  is the fileset gone from the default branch again after the merge — a revert — and the record names the
  objects the definition left running on the installation for a person to delete; the manager deletes
  nothing.
- **Waiting for the customer** is not a failure: a customer action from the dry run is open — name it and
  its installation; the customer's people close it, and the next watch or verify moves the state on.
- **Failed** names the pull request, installation or probe that failed in the result's message; relay it
  and stop. A pull request a failure left open is closed by `deny_action`, a member's call. Trying again is
  a new dry run and a new confirmation of the person's, never yours.
- **A wave** is one action over N installations with one approval, rolled out one stage per `merge_action`:
  the next installation's pull requests merge only once the one in flight is *enabled*; a red probe stops it
  — that installation *failed*, the stages after it not started, their pull requests open — and a stage
  *waiting for the customer* holds it. Read the rollout per installation and say which are done, which are
  pending, which stopped it, and which the dry run had skipped.
- **No action record readable** — `get_info` says the action reader is not configured — means the history
  is not available here; say so. The pull requests still exist under the person's name on GitHub.

## What you do, and what you never do

You read the record when asked and relay it. `merge_action` is the actor's own step: when the person asks
you to merge their approved action, call it once as them and relay the answer — a pull request whose checks
are still pending stops the call, and the person asks again later; never unasked, never in a loop.
`watch_action` is one call per ask, the picture as it is now; never a loop, never a schedule. You never
approve or deny — the buttons are a second person's — never re-request a review, never merge, push or
comment around the manager, and never restart an action.
