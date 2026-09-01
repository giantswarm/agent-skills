# Severity and disposition rubric

Two separate judgements. **Severity** is how bad it would be. **Disposition** is
what the engineer should do about it now. Confusing them is the most common way
an audit becomes noise: a genuinely severe risk that is out of scope for this
change does not belong in the same bucket as a blocking defect.

## Severity

Severity is likelihood times impact, bounded below by the policy's
`severity_floor`. A finding can be rated above the floor, never below it.

**Likelihood** given the plan as written:

| | |
| --- | --- |
| Near certain | the plan as written produces this condition |
| Likely | ordinary operation reaches it without anything going wrong |
| Possible | needs a mistake, a specific input, or an insider |
| Unlikely | needs a chain of conditions or a determined attacker with position |

**Impact** at Aurelia:

| | |
| --- | --- |
| Severe | customer funds or personal data exposed or lost; regulatory reportable; an important business function down beyond its RTO |
| Major | material internal exposure, a control that auditors rely on defeated, PCI or EU-residency boundary crossed |
| Moderate | a control weakened without immediate exposure; detection or recovery degraded |
| Minor | hygiene, defence in depth, no realistic path to harm on its own |

| | Severe | Major | Moderate | Minor |
| --- | --- | --- | --- | --- |
| **Near certain** | Critical | Critical | High | Medium |
| **Likely** | Critical | High | Medium | Low |
| **Possible** | High | High | Medium | Low |
| **Unlikely** | High | Medium | Low | Low |

State the likelihood and impact you chose. A severity with no visible reasoning
is unarguable, and an engineer who cannot argue with a finding cannot act on it
either.

## Disposition

Four buckets. Every finding gets exactly one.

**Address before merge.** A blocking policy is violated and nothing covers it.
The change cannot ship in this form. Reserve this for `blocking = yes` policies
with no live cover, and say which policy and why cover does not apply. Being
wrong here is expensive in credibility, so check the ruling register first.

**Address in this change.** Real, in scope, fixable here, not worth stopping the
merge for on its own. Most High and Medium findings land here.

**Investigate.** The plan does not say enough to judge. The honest output is a
specific question, not a guessed severity. Name what would change the answer:
"if the buffer can contain unmasked PANs this is Critical, if it is reference
data only it is Low, and the issue does not say."

**Keep in mind.** Real but outside this change: a downstream consequence, a
pattern worth watching, an adjacent system that will need the same treatment.
Never used as a soft landing for something that belongs in a harder bucket.

## Cover: check before you raise

The ruling register is authoritative on what has already been decided. Before
raising anything, check it, because these change the finding entirely:

- **Live exception or accepted risk** covering this exact condition. Not a
  finding. Note that cover exists, quote the ruling, and give its expiry.
- **Cover that is expiring.** A dependency on an exception that lapses inside 90
  days is itself a finding, and its severity is the severity of the underlying
  policy on the day cover ends.
- **Cover that has expired.** Treat as uncovered, and say when it lapsed.
- **Cover whose conditions this plan exceeds.** An exception granted for two
  partners does not cover five. Read the rationale, not just the policy ID.
- **Prior rejection of the same pattern.** The board has already ruled. Say so,
  quote it, and state what the board required instead. Re-proposing a rejected
  pattern without addressing the stated reason is a finding in its own right.
- **Repeat findings across teams.** The same policy failing for a third time is
  systemic. Say that plainly: the fix is not another ticket.

## Proportionality

The audit is judged on whether an engineer acts on it. Two failure modes destroy
that, and the second is the more common.

**Under-calling** a Critical because the plan is short or the team is trusted.

**Over-calling** everything, which trains people to skim. A plan that reduces
risk should be told so, in the first line, before any finding. Do not
manufacture findings to look thorough. Do not raise a Low on every audit out of
habit. Five findings that all matter beat fifteen that mostly do not, and if the
honest answer is "two things, both small", that is the answer.
