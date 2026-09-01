# Framework mapping and how to cite it

Aurelia's own policy IDs are primary. Frameworks are the mapping, not the
source: findings are raised against `ASP-*` policies, and the framework
references travel with them so the report doubles as evidence.

The per-policy mapping lives in the policy register (`iso_27001_2022_controls`,
`dora_articles`, `other_references`). Read it from there rather than reasoning
about it, and cite exactly what it says.

## ISO/IEC 27001:2022 Annex A

93 controls in four themes. Aurelia has been certified since 2019 and is
recertified on a three-year cycle.

| Theme | Range |
| --- | --- |
| Organizational | A.5.1 to A.5.37 |
| People | A.6.1 to A.6.8 |
| Physical | A.7.1 to A.7.14 |
| Technological | A.8.1 to A.8.34 |

Cite as `ISO/IEC 27001:2022 A.8.24`. The 2022 revision renumbered everything
from the 2013 edition, so a control number without the year is ambiguous and
older internal documents may use the old numbering.

## DORA, Regulation (EU) 2022/2554

Applies to Aurelia as a credit institution, in force since January 2025.
Supervised by BaFin. The articles that bear on platform changes:

| Article | Subject |
| --- | --- |
| Art. 5 | Governance and organisation; the management body owns ICT risk |
| Art. 6 | ICT risk management framework; documented, reviewed at least annually |
| Art. 8 | Identification; classification of assets and dependencies |
| Art. 9 | Protection and prevention; access control, encryption, patching, change management tied to risk assessment |
| Art. 10 | Detection; mechanisms for anomalous activity, tested, with escalation |
| Art. 11 | Response and recovery; continuity plans, tested |
| Art. 12 | Backup, restoration and recovery; RTO and RPO defined and tested |
| Art. 13 | Learning and evolving; post-incident review feeding the framework |
| Art. 14 | Crisis communication |
| Art. 28 to 30 | ICT third-party risk; register of information, contractual requirements, exit strategies |

Cite as `DORA Art. 9`. Two DORA points come up constantly and are worth stating
plainly in findings because engineers routinely miss them:

- **Art. 9 makes the risk assessment part of the change**, not a document
  produced afterwards. An assessment dated after the merge does not satisfy it.
- **Art. 28 to 30 make a new external ICT dependency a registrable event.**
  Adopting a managed service is not purely an engineering decision, and the exit
  strategy is a precondition rather than a follow-up.

## Others

- **PCI DSS v4.0** applies only to the cardholder data environment. Cite by
  requirement number (`PCI DSS Requirement 1`). Anything crossing the CDE
  boundary needs Compliance, not this audit, to sign off.
- **GDPR** for personal data: lawful basis, minimisation, retention, transfers.
  Cite by article. Transfers outside the EU need the DPO.
- **CIS Kubernetes Benchmark** for cluster hardening. Cite by section title
  ("CIS Kubernetes Benchmark, RBAC and Service Accounts") rather than by
  decimal, because sub-section numbering shifts between benchmark versions and a
  stale decimal is worse than a title.

## Honesty about mapping

Map only what the policy register maps. Do not invent a control number to make a
finding look better evidenced, and do not stretch a control to cover something
it does not. If a finding has no framework mapping, it is still a valid finding
against Aurelia policy; say that and leave the mapping blank.

Where a finding is genuinely regulatory rather than internal, say which
regulator's expectation is at stake and route it to Compliance. Platform
engineers should not be the ones deciding whether something is reportable.
