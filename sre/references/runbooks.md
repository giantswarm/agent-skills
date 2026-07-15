# Runbooks

A runbook is a focused operational document that tells a responder how to handle
one specific situation — usually the situation an alert describes. A good runbook
turns "I've been paged and I don't know where to start" into a sequence of safe,
concrete steps.

## What makes a good runbook

- **Scoped to one problem.** One alert or one operational task per runbook.
  Sprawling "everything about X" documents are references, not runbooks.
- **Starts with orientation.** What does this alert/condition mean? What is the
  likely impact? How urgent is it?
- **Read-only triage first.** The first steps confirm the situation and gather
  data before anything changes — mirroring the non-invasive principle.
- **Safe, copy-pasteable commands.** Commands should be correct and safe to run
  as written. Mark any mutating/destructive step clearly and state its effect.
- **Decision points, not just steps.** "If you see A, do X; if you see B, do Y."
- **An escalation path.** When and to whom to escalate if the runbook does not
  resolve it.
- **Maintained.** Runbooks rot. They carry an owner and a last-reviewed date, and
  are updated when the system changes.

## Recommended structure

```markdown
# <Alert or task name>

## What this means
Plain-language explanation of the condition and its typical cause.

## Impact
Who/what is affected and how urgent this is.

## Triage (read-only)
1. Confirm the condition (query / dashboard / kubectl).
2. Assess scope and recent changes.
3. Gather the key signals.

## Diagnosis
Decision tree: common causes and how to distinguish them.

## Remediation
Ordered, safe steps. Mutating steps clearly marked with expected effect + rollback.

## Escalation
When to escalate, and to whom.

## References
Dashboards, related alerts, related runbooks.
```

## Conventions worth adopting

- **Frontmatter/metadata.** Give each runbook a title, a short description, an
  owner, and a last-reviewed date so staleness is visible.
- **Parameterize environment specifics.** Refer to targets through variables
  (e.g. `$CLUSTER`, `$NAMESPACE`, a context variable) rather than hard-coding a
  specific cluster, context, or hostname. This keeps runbooks reusable and avoids
  baking in environment-specific or sensitive values.
- **Be explicit about context.** For multi-cluster setups, make every command
  state which cluster/context it targets (e.g. pass `--context` explicitly)
  instead of relying on ambient current-context.
- **Link, don't duplicate.** Point at dashboards and related runbooks rather than
  copying their content, so there is a single source of truth.
- **Keep secrets out.** Never embed credentials, tokens, or personal/customer
  data in a runbook.

## Quality checklist

Before publishing or reviewing a runbook, confirm:

- [ ] Scoped to a single alert or task.
- [ ] Opens with meaning + impact + urgency.
- [ ] Triage steps are read-only and come first.
- [ ] Commands are correct, safe, and use variables for environment specifics.
- [ ] Mutating steps are clearly marked with expected effect and rollback.
- [ ] Includes a decision tree for the common causes.
- [ ] Has an escalation path.
- [ ] Has an owner and a last-reviewed date.
- [ ] Contains no secrets or environment-specific sensitive values.
