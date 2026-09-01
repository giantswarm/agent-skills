#!/usr/bin/env python3
"""
Build the Aurelia Bank security policy corpus (fictional).

The policy register and the ruling register are authored here rather than
generated, so this script is the single place to edit them. It writes
data/policies.csv and data/rulings.csv with correct CSV quoting.

    python3 scripts/build_corpus.py

External framework references are real: ISO/IEC 27001:2022 Annex A control
numbers and DORA (Regulation (EU) 2022/2554) article numbers. CIS Kubernetes
Benchmark items are cited by section title, not by decimal, because the
sub-section numbering shifts between benchmark versions.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data"))
os.makedirs(OUT, exist_ok=True)

# policy_id, domain, title, requirement, severity_floor, blocking, iso, dora, other, owner, reviewed
POLICIES = [
    # ---------------- Identity and access management
    ("ASP-IAM-01", "IAM", "Human access to production is time-bound and approved",
     "Standing human access to production namespaces is prohibited. Access is granted just-in-time "
     "for a named change or incident, expires within 8 hours, and is approved by someone other than "
     "the requester.",
     "High", "yes", "A.5.15; A.5.18; A.8.2", "Art. 9", "", "Security Architecture", "2026-05-14"),
    ("ASP-IAM-02", "IAM", "Workload identity is federated, never a long-lived credential",
     "Workloads authenticate to cloud services and internal APIs using short-lived federated "
     "identity (OIDC / workload identity). Long-lived static credentials issued to a workload are "
     "prohibited, including in secret managers.",
     "High", "yes", "A.5.16; A.8.2; A.8.24", "Art. 9", "", "Security Architecture", "2026-05-14"),
    ("ASP-IAM-03", "IAM", "Least privilege on Kubernetes RBAC",
     "ServiceAccounts are scoped to a single namespace and to the verbs the workload needs. "
     "cluster-admin, wildcard verbs and wildcard resources are prohibited outside the platform "
     "team's own control-plane tooling.",
     "High", "yes", "A.5.15; A.8.2", "Art. 9",
     "CIS Kubernetes Benchmark, RBAC and Service Accounts", "Platform Security", "2026-04-02"),
    ("ASP-IAM-04", "IAM", "Break-glass credentials are held offline and alarmed",
     "Break-glass accounts exist for each production cluster, are stored offline, and every use "
     "raises an immediate alert to the on-call security engineer.",
     "Medium", "no", "A.8.2", "Art. 9; Art. 10", "", "Security Architecture", "2026-05-14"),
    # ---------------- Cryptography
    ("ASP-CRY-01", "CRYPTO", "Mutual TLS on all service-to-service traffic",
     "Traffic between services inside the platform is mutually authenticated with TLS 1.3. "
     "Plaintext internal traffic is prohibited, including within a single cluster or namespace.",
     "High", "yes", "A.8.20; A.8.24", "Art. 9", "", "Security Architecture", "2026-05-14"),
    ("ASP-CRY-02", "CRYPTO", "Customer data is encrypted at rest with bank-managed keys",
     "Data classified Confidential or above is encrypted at rest using keys held in the bank's own "
     "KMS. Provider-managed keys are not acceptable for customer financial data.",
     "High", "yes", "A.8.24", "Art. 9", "", "Security Architecture", "2026-03-11"),
    ("ASP-CRY-03", "CRYPTO", "Certificate lifetimes do not exceed 90 days",
     "TLS certificates issued by the internal CA expire within 90 days and are renewed "
     "automatically. Manual renewal is prohibited for anything in the request path.",
     "Medium", "no", "A.8.24", "Art. 9", "", "Platform Security", "2026-04-02"),
    ("ASP-CRY-04", "CRYPTO", "Secrets are never carried in environment variables or images",
     "Secrets are mounted from the secret manager at runtime. Secrets in environment variables, "
     "container images, Helm values, or git are prohibited regardless of repository visibility.",
     "Critical", "yes", "A.8.24; A.8.12", "Art. 9", "", "Security Architecture", "2026-05-14"),
    # ---------------- Network
    ("ASP-NET-01", "NETWORK", "Default-deny network policy in every namespace",
     "Every namespace carries a default-deny NetworkPolicy for ingress and egress. Permitted flows "
     "are declared explicitly and reviewed when they change.",
     "High", "yes", "A.8.20; A.8.22", "Art. 9",
     "CIS Kubernetes Benchmark, Network Policies and CNI", "Platform Security", "2026-04-02"),
    ("ASP-NET-02", "NETWORK", "External exposure goes through the managed edge only",
     "Services reachable from outside the bank are published through the managed API gateway, which "
     "provides authentication, rate limiting, WAF and request logging. Direct LoadBalancer or "
     "NodePort exposure of an application is prohibited.",
     "Critical", "yes", "A.8.20; A.8.22", "Art. 9; Art. 10", "", "Security Architecture", "2026-05-14"),
    ("ASP-NET-03", "NETWORK", "Cardholder data environment is network-segregated",
     "Workloads in PCI scope run in dedicated clusters with no shared network path to non-PCI "
     "workloads. Any flow crossing the boundary requires a documented segmentation review.",
     "Critical", "yes", "A.8.22", "Art. 9", "PCI DSS Requirement 1", "Compliance", "2026-02-19"),
    ("ASP-NET-04", "NETWORK", "Egress to the internet is allow-listed",
     "Production workloads reach external destinations through the egress proxy against an "
     "allow-list. Unrestricted egress is prohibited.",
     "High", "yes", "A.8.20; A.8.22", "Art. 9", "", "Platform Security", "2026-04-02"),
    # ---------------- Data protection
    ("ASP-DAT-01", "DATA", "Data classification is declared before a store is provisioned",
     "Every data store carries a classification (Public, Internal, Confidential, Restricted) and a "
     "named data owner before it is created. Undeclared stores are treated as Restricted.",
     "Medium", "yes", "A.5.12; A.5.13", "Art. 8", "", "Data Governance", "2026-01-30"),
    ("ASP-DAT-02", "DATA", "Personal and payment data is masked outside production",
     "Non-production environments never hold real personal or payment data. Data used for testing "
     "or analysis is masked, tokenised or synthetic.",
     "Critical", "yes", "A.8.11; A.8.33", "Art. 9", "GDPR Art. 32; PCI DSS Requirement 3",
     "Data Governance", "2026-01-30"),
    ("ASP-DAT-03", "DATA", "Personal data does not enter logs, traces or metrics",
     "Telemetry must not contain personal data, authentication material, primary account numbers or "
     "full request or response bodies. Field-level redaction is applied at the emitting service.",
     "High", "yes", "A.8.11; A.8.12; A.8.15", "Art. 9; Art. 10",
     "GDPR Art. 5(1)(c)", "Security Architecture", "2026-05-14"),
    ("ASP-DAT-04", "DATA", "Customer data stays in the EU",
     "Customer data is processed and stored within the EU or EEA. Any processing outside requires a "
     "transfer assessment approved by the DPO before the change ships.",
     "Critical", "yes", "A.5.34", "Art. 28", "GDPR Chapter V", "Compliance", "2026-02-19"),
    ("ASP-DAT-05", "DATA", "Retention is declared and enforced technically",
     "Every data store declares a retention period with an enforcing mechanism. Indefinite "
     "retention of personal data is prohibited.",
     "Medium", "no", "A.5.33; A.8.10", "Art. 8", "GDPR Art. 5(1)(e)", "Data Governance", "2026-01-30"),
    # ---------------- Logging and detection
    ("ASP-LOG-01", "LOGGING", "Security-relevant events are shipped to the central SIEM",
     "Authentication, authorisation failures, privileged actions and configuration changes are "
     "shipped to the central SIEM within 5 minutes and retained 400 days.",
     "High", "yes", "A.8.15; A.8.16", "Art. 10", "", "Security Operations", "2026-04-24"),
    ("ASP-LOG-02", "LOGGING", "Audit logs are tamper-evident and separately controlled",
     "Audit logs are append-only and cannot be modified or deleted by the workloads or operators "
     "they describe.",
     "High", "yes", "A.8.15", "Art. 10; Art. 13", "", "Security Operations", "2026-04-24"),
    ("ASP-LOG-03", "LOGGING", "New external surfaces have detection before go-live",
     "A newly exposed external interface has alerting for authentication failure spikes, anomalous "
     "volume and error-rate deviation in place before it serves production traffic.",
     "High", "yes", "A.8.16", "Art. 10", "", "Security Operations", "2026-04-24"),
    # ---------------- Supply chain and change
    ("ASP-SUP-01", "SUPPLY_CHAIN", "Container images are signed and admitted by policy",
     "Only images signed by the bank's build system are admitted to production clusters, enforced "
     "at admission. Images from public registries are mirrored and rescanned first.",
     "High", "yes", "A.8.28; A.8.31", "Art. 9",
     "CIS Kubernetes Benchmark, General Policies", "Platform Security", "2026-04-02"),
    ("ASP-SUP-02", "SUPPLY_CHAIN", "CI credentials are not shared across teams",
     "Build credentials are scoped to one team's pipelines. Shared runners must isolate credentials "
     "and workspaces per job so one team's build cannot read another's material.",
     "High", "yes", "A.5.15; A.8.2; A.8.31", "Art. 9", "", "Platform Security", "2026-04-02"),
    ("ASP-SUP-03", "SUPPLY_CHAIN", "Critical and high vulnerabilities are remediated on a clock",
     "Critical vulnerabilities in production images are remediated within 7 days, high within 30. "
     "An unremediated critical past 7 days blocks further deploys of that component.",
     "High", "no", "A.8.8", "Art. 9", "", "Security Operations", "2026-04-24"),
    ("ASP-CHG-01", "CHANGE", "Security-relevant changes carry a recorded risk assessment",
     "A change that alters an external surface, an authorisation boundary, a data classification, or "
     "a cryptographic control carries a documented risk assessment linked to the change record "
     "before merge.",
     "High", "yes", "A.8.32", "Art. 9; Art. 6", "", "Security Architecture", "2026-05-14"),
    ("ASP-CHG-02", "CHANGE", "Production changes are reversible and the rollback is tested",
     "Every production change has a documented rollback that has been exercised in a "
     "pre-production environment.",
     "Medium", "no", "A.8.32", "Art. 11; Art. 12", "", "Platform Security", "2026-04-02"),
    # ---------------- Third party and resilience
    ("ASP-TPR-01", "THIRD_PARTY", "New ICT providers pass third-party risk assessment first",
     "Any new external ICT service supporting an important business function completes third-party "
     "risk assessment and is entered in the register of information before production use.",
     "Critical", "yes", "A.5.19; A.5.21; A.5.23", "Art. 28; Art. 29; Art. 30",
     "", "Compliance", "2026-02-19"),
    ("ASP-TPR-02", "THIRD_PARTY", "Every provider dependency has a documented exit strategy",
     "Cloud and SaaS dependencies supporting an important business function carry a tested exit "
     "plan, including data extraction format and an estimated migration window.",
     "High", "yes", "A.5.23", "Art. 28", "", "Compliance", "2026-02-19"),
    ("ASP-RES-01", "RESILIENCE", "Backups are tested by restore, not by job status",
     "Backup validity is proven by a restore into an isolated environment at least quarterly. "
     "A successful backup job is not evidence of a working backup.",
     "High", "yes", "A.8.13", "Art. 12", "", "Platform Security", "2026-04-02"),
    ("ASP-RES-02", "RESILIENCE", "Important business functions have stated RTO and RPO",
     "Services supporting an important business function declare recovery time and recovery point "
     "objectives, and the design is demonstrably capable of meeting them.",
     "High", "yes", "A.5.29; A.5.30", "Art. 11; Art. 12", "", "Compliance", "2026-02-19"),
]

FIELDS = ["policy_id", "domain", "title", "requirement", "severity_floor", "blocking",
          "iso_27001_2022_controls", "dora_articles", "other_references", "owner",
          "last_reviewed"]

with open(os.path.join(OUT, "policies.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(FIELDS)
    for row in POLICIES:
        w.writerow(row)
print("policies.csv            %3d rows" % len(POLICIES))


# ------------------------------------------------------------ ruling register
# Past decisions of the Security Architecture Review Board. This is what makes
# an audit company-specific rather than a generic checklist: a finding already
# covered by a live exception is not a new finding, and a finding raised for the
# third time across three teams is a systemic problem, not a ticket.
#
# decision: EXCEPTION_GRANTED | RISK_ACCEPTED | REJECTED | CONDITIONS_APPLIED | REMEDIATED
RULINGS = [
    ("EXC-2025-014", "2025-10-02", "EPIC-3980", "ASP-NET-02", "EXCEPTION_GRANTED", "Critical",
     "2026-09-30",
     "Partner-bank pilot permitted to terminate TLS at a dedicated ingress outside the managed edge, "
     "because the gateway did not yet support the partner's client-certificate scheme. Conditional on "
     "the pilot staying at two partners and on migration to the managed edge before expiry.",
     "S. Okonkwo (CISO delegate)", "Payments Platform"),
    ("RUL-2025-031", "2025-11-18", "EPIC-4103", "ASP-DAT-02", "REJECTED", "Critical", "",
     "Request for the analytics group to query the production data lake directly was rejected. "
     "Board position: analytical access is served by the masked replica, not by read access to "
     "production. Re-proposals must show masking at the source, not access controls on top.",
     "Security Architecture Review Board", "Data Platform"),
    ("RUL-2025-022", "2025-08-27", "EPIC-3844", "ASP-SUP-02", "CONDITIONS_APPLIED", "High", "",
     "Shared build runners approved for two teams on condition of per-job credential scoping and "
     "workspace teardown between jobs. Conditions were implemented for those two teams only.",
     "Security Architecture Review Board", "Developer Experience"),
    ("RUL-2026-004", "2026-02-11", "EPIC-4211", "ASP-SUP-02", "REJECTED", "High", "",
     "Second request to widen the shared runner pool rejected: the per-job isolation from "
     "RUL-2025-022 was found not to be in place, so the original conditions were never met. "
     "Any further request must evidence isolation before approval, not promise it.",
     "Security Architecture Review Board", "Developer Experience"),
    ("RSK-2025-009", "2025-06-30", "EPIC-3712", "ASP-CRY-03", "RISK_ACCEPTED", "Medium",
     "2026-12-31",
     "The legacy settlement adapter cannot rotate certificates automatically and runs on 12-month "
     "certificates. Risk accepted until the adapter is decommissioned or the internal CA migration "
     "lands, whichever is first.",
     "S. Okonkwo (CISO delegate)", "Core Banking"),
    ("RSK-2026-002", "2026-01-22", "EPIC-4155", "ASP-DAT-05", "RISK_ACCEPTED", "Medium",
     "2027-03-31",
     "Observability stack retains trace data for 30 days against a declared 14-day target, because "
     "the storage tier cannot express per-signal retention. Accepted on the basis that traces carry "
     "no personal data. Acceptance is void if that ceases to hold.",
     "Security Architecture Review Board", "Observability"),
    ("RUL-2026-011", "2026-03-19", "EPIC-4260", "ASP-TPR-01", "CONDITIONS_APPLIED", "Critical", "",
     "Managed message broker approved subject to entry in the register of information and an exit "
     "plan with a stated extraction format. Precedent: managed data services are approvable, but "
     "the exit plan is a precondition and not a follow-up.",
     "Compliance", "Payments Platform"),
    ("RUL-2026-018", "2026-05-06", "EPIC-4318", "ASP-DAT-03", "REMEDIATED", "High", "",
     "Full request bodies were found in the payments service logs during a review. Redaction was "
     "implemented at the emitting service. Precedent for scope: redaction belongs at the emitter, "
     "not in the log pipeline, because the pipeline is not a trust boundary.",
     "Security Architecture Review Board", "Payments Platform"),
    ("RUL-2026-023", "2026-06-24", "EPIC-4351", "ASP-IAM-02", "REJECTED", "High", "",
     "Proposal to store a long-lived cloud access key in the secret manager was rejected. The secret "
     "manager is not a mitigation for a long-lived credential; federation was available and was "
     "required instead.",
     "Security Architecture Review Board", "Data Platform"),
    ("RSK-2026-007", "2026-04-15", "EPIC-4289", "ASP-SUP-03", "RISK_ACCEPTED", "High",
     "2026-10-31",
     "Two high-severity vulnerabilities in the vendor-supplied fraud-scoring image cannot be patched "
     "before the vendor's next release. Compensating controls: egress restriction and additional "
     "runtime monitoring.",
     "S. Okonkwo (CISO delegate)", "Fraud"),
    ("RUL-2026-029", "2026-07-08", "EPIC-4372", "ASP-NET-03", "CONDITIONS_APPLIED", "Critical", "",
     "A reporting flow crossing out of the cardholder data environment was approved subject to "
     "tokenisation before the boundary and a segmentation test. Precedent: PCI boundary crossings "
     "are approvable only with tokenisation at source.",
     "Compliance", "Payments Platform"),
    ("RUL-2026-033", "2026-07-29", "EPIC-4390", "ASP-RES-01", "REMEDIATED", "High", "",
     "Quarterly restore test for the customer ledger had never actually been run; the job monitor "
     "was green because the backup job succeeded. Restore drill is now scheduled and evidenced.",
     "Platform Security", "Core Banking"),
    ("RUL-2026-036", "2026-08-12", "EPIC-4402", "ASP-CHG-01", "CONDITIONS_APPLIED", "High", "",
     "Reminder issued to all platform teams: a risk assessment recorded after merge does not satisfy "
     "ASP-CHG-01. Several changes in Q2 carried assessments dated after the merge commit.",
     "Security Architecture Review Board", "All platform teams"),
    ("EXC-2026-005", "2026-03-04", "EPIC-4240", "ASP-NET-04", "EXCEPTION_GRANTED", "High",
     "2026-11-30",
     "The market-data ingest service requires egress to a provider IP range that changes without "
     "notice, so a hostname-based allow-list is used instead of the standard IP allow-list. Reviewed "
     "at expiry.",
     "Platform Security", "Market Data"),
    ("RUL-2025-040", "2025-12-16", "EPIC-4128", "ASP-CRY-01", "CONDITIONS_APPLIED", "High", "",
     "Service mesh mTLS rollout approved in permissive mode for one quarter to allow migration, on "
     "condition of a dated cutover to strict mode. Precedent: permissive mTLS is a migration state "
     "with an end date, not a resting state.",
     "Security Architecture Review Board", "Platform"),
    ("RSK-2025-015", "2025-09-10", "EPIC-3901", "ASP-IAM-01", "RISK_ACCEPTED", "High",
     "2026-06-30",
     "Standing production access retained for four named core-banking engineers during the mainframe "
     "offload, because just-in-time tooling did not cover the legacy estate. EXPIRED without renewal.",
     "S. Okonkwo (CISO delegate)", "Core Banking"),
]

RULING_FIELDS = ["ruling_id", "decided_on", "issue_ref", "policy_id", "decision",
                 "severity_at_time", "expires_on", "rationale", "decided_by", "team"]

with open(os.path.join(OUT, "rulings.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(RULING_FIELDS)
    for row in RULINGS:
        w.writerow(row)
print("rulings.csv             %3d rows" % len(RULINGS))
print("\ncorpus written to %s" % OUT)


# ------------------------------------------------------------------- backlog
# The change backlog, so the agent can answer "what am I working on" and "what
# still needs auditing" as a lookup rather than by reading a directory. Items
# with a body_file have a written plan the agent can audit; the closed ones
# carry the audit outcome and tie back to the ruling register.
BACKLOG = [
    ("EPIC-4412", "Open the Payments API to three additional partner banks",
     "Payments Platform", "J. Vandermeer", "In progress", "High", "Q4 2026",
     "2026-08-28", "NOT_AUDITED", "",
     "EPIC-4412-partner-api-expansion.md"),
    ("EPIC-4423", "Add a /debug endpoint to the ingest service",
     "Payments Platform", "T. Halloran", "In progress", "Medium", "Next sprint",
     "2026-08-30", "NOT_AUDITED", "",
     "EPIC-4423-ingest-debug-endpoint.md"),
    ("EPIC-4387", "Move the customer ledger read replica to a managed cloud database",
     "Core Banking", "A. Brummer", "In progress", "High", "Q4 2026",
     "2026-08-26", "NOT_AUDITED", "",
     "EPIC-4387-managed-ledger-replica.md"),
    ("EPIC-4401", "Give the analytics group query access to the production data lake",
     "Data Platform", "R. Feldkamp", "In review", "High", "Q4 2026",
     "2026-08-29", "NOT_AUDITED", "",
     "EPIC-4401-analytics-data-lake-access.md"),
    ("EPIC-4396", "Enable full-fidelity tracing on the payments path",
     "Observability", "M. Sandoval", "In progress", "Medium", "Q4 2026",
     "2026-08-27", "NOT_AUDITED", "",
     "EPIC-4396-full-fidelity-tracing.md"),
    ("EPIC-4370", "Consolidate CI onto a shared runner pool for all teams",
     "Developer Experience", "K. Osei", "In review", "Medium", "Q4 2026",
     "2026-08-25", "NOT_AUDITED", "",
     "EPIC-4370-shared-ci-runners.md"),
    ("EPIC-4431", "Migrate to the new internal CA with 30-day certificate lifetimes",
     "Platform Security", "L. Achterberg", "In progress", "Medium", "Q4 2026",
     "2026-08-31", "NOT_AUDITED", "",
     "EPIC-4431-internal-ca-migration.md"),
    # Closed items, audited previously. These are why the ruling register has
    # entries, and they let the agent answer questions about audit history.
    ("EPIC-4402", "Quarterly access recertification tooling",
     "Platform Security", "L. Achterberg", "Done", "Medium", "Q3 2026",
     "2026-08-14", "AUDITED_PROCEED_WITH_CHANGES", "RUL-2026-036", ""),
    ("EPIC-4390", "Customer ledger restore drill automation",
     "Core Banking", "A. Brummer", "Done", "High", "Q3 2026",
     "2026-08-01", "AUDITED_PROCEED_WITH_CHANGES", "RUL-2026-033", ""),
    ("EPIC-4372", "Monthly card reporting extract for finance",
     "Payments Platform", "J. Vandermeer", "Done", "High", "Q3 2026",
     "2026-07-11", "AUDITED_PROCEED_WITH_CHANGES", "RUL-2026-029", ""),
    ("EPIC-4351", "Cloud access key rotation for the data platform",
     "Data Platform", "R. Feldkamp", "Blocked", "High", "Q3 2026",
     "2026-06-26", "AUDITED_BLOCKED", "RUL-2026-023", ""),
    ("EPIC-4318", "Payments service structured logging rollout",
     "Payments Platform", "T. Halloran", "Done", "Medium", "Q2 2026",
     "2026-05-08", "AUDITED_PROCEED_WITH_CHANGES", "RUL-2026-018", ""),
]

BACKLOG_FIELDS = ["issue_ref", "title", "team", "reporter", "status", "priority",
                  "target", "last_updated", "audit_status", "related_ruling", "body_file"]

with open(os.path.join(OUT, "backlog.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(BACKLOG_FIELDS)
    for row in BACKLOG:
        w.writerow(row)
print("backlog.csv             %3d rows" % len(BACKLOG))
