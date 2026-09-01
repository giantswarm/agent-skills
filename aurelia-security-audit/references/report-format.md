# Audit report format

One report per audit. It is written for the engineer who wrote the issue, and it
is also the artifact the review board and the auditors read later, so it has to
work for both without becoming a compliance document nobody wants to read.

## Header

```
Security audit: EPIC-4412 Open the Payments API to three additional partner banks
Audited: 2026-09-01   Team: Payments Platform   Auditor: Argus (automated pre-review)
Verdict: Blocked, 3 findings to address before merge
Policies checked: 12   Findings: 8 (2 Critical, 3 High, 2 Medium, 1 Low)
```

The verdict line is one of:

- **Blocked** with the count of before-merge findings
- **Proceed with changes**, when findings exist but none block
- **Proceed**, when nothing material was found
- **Insufficient detail to audit**, when the plan does not say enough to judge
  the parts that matter. This is a legitimate verdict and it beats guessing.

## Summary

Three to five sentences of plain prose. What the change does, the single most
important thing to fix, and whether anything here needs a human security
architect rather than the engineer. Where the change improves the security
posture, say that first.

No finding tables in the summary. The engineer reads this part properly.

## Findings

Grouped by disposition in this order: Address before merge, Address in this
change, Investigate, Keep in mind. Within a group, highest severity first.

Each finding:

```
### F1. Partner API keys carried in the deployment environment
Severity: Critical (near certain / severe)   Policy: ASP-CRY-04 (blocking)
Maps to: ISO/IEC 27001:2022 A.8.24, A.8.12 | DORA Art. 9

What the plan says: keys are read from PARTNER_API_KEYS in the deployment
environment as a comma-separated list, and adding a partner is a values change.

Why it matters: the key is then in the Helm values, in git history, in the
rendered manifest, and readable by anyone who can describe the Deployment or
read the release. Revocation means a redeploy of every partner's key at once.

What would resolve it: per-partner credentials in the secret manager, mounted at
runtime, rotatable independently. If partner middleware cannot do client
certificates, that constraint belongs in the issue explicitly.
```

Rules for findings:

- **Quote or closely paraphrase the plan.** A finding that cannot be traced to a
  line in the issue reads as invented and will be dismissed.
- **Cite the policy ID and the framework mapping.** The mapping is what makes
  the report usable as evidence.
- **Say what would resolve it**, concretely enough to act on. Not "apply least
  privilege" but "scope the ServiceAccount to the namespace and drop the
  wildcard on secrets".
- **Do not prescribe an implementation** the plan has not chosen. Describe the
  property that must hold and let the engineer pick.
- Show likelihood and impact next to the severity.

## Cover and precedent

A short section, only when relevant, and it usually is. Three things belong here:

- Live exceptions or accepted risks this change relies on, with expiry dates and
  whether the plan stays inside their conditions
- Prior board rulings on this pattern, quoted, with what the board required
- Repeat findings, naming the earlier rulings and the other teams affected

This section is where the audit stops being a checklist. An engineer can find a
policy themselves; they cannot know that the board rejected this exact shape ten
months ago and why.

## Compliance coverage

A compact table of the policies checked, their framework mappings, and the
outcome (pass, finding, not applicable, insufficient detail). Include the passes.
An auditor's question is "what did you check", not only "what did you find", and
a report that lists only failures cannot answer it.

## What was not assessed

Explicit and short. The audit reads a plan, not a system: it cannot see the
code, the running configuration, the actual IAM state, or anything the issue does
not mention. Say so, and name the specific unknowns that would most change the
verdict. This is what stops the report being mistaken for assurance.

## Length

A clean plan is under a page. A plan with eight findings is two to three. If it
runs longer, the plan probably needs a conversation rather than a longer report,
and saying that is more useful than writing it.
