# Beacon production, nationwide and compliance readiness register

This register is a release-control document, not a representation that Beacon is
HIPAA compliant, CJIS authorized, or approved by any agency. Technical evidence,
organizational policies, contracts, deployment evidence and agency authorization
must all be complete before a production claim is made.

Status values are `implemented`, `verification required`, `external decision`,
and `blocked`. Every verification item needs an owner, date and evidence link in
the release record.

## Release-blocking controls

| Control | Current status | Required evidence before production |
| --- | --- | --- |
| Tenant isolation | Implemented; verification required | PostgreSQL RLS tests, cross-agency authorization report, database-role posture output |
| Production MFA | Implemented; verification required | Migration `3d6a02b9e841`, staging enrollment/refresh tests, recovery exercise, legacy-session revocation evidence |
| Encryption in transit | Implemented in part; verification required | PostgreSQL `verify-full` startup evidence, approved TLS termination configuration, certificate rotation, internal service encryption decision |
| Encryption at rest | Implemented in part; verification required | S3 default and per-upload KMS checks, database and backup encryption configuration with key identifiers |
| Key and secret management | Implemented in part; verification required | KMS ARN/account validation, access policy, rotation evidence, secret-manager inventory and break-glass procedure |
| Audit integrity and retention | Verification required | Central immutable destination, access controls, clock synchronization and approved retention |
| Backups and recovery | Verification required | Encrypted backups, point-in-time recovery, successful timed restoration exercise |
| High availability | Verification required | Multi-instance API and worker tests, load balancer health, zone/region failure decision |
| Monitoring and incident alerting | Verification required | Scrape configuration, alert destinations, on-call ownership and alert exercise |
| External alert delivery | Blocked on provider selection | Provider contract, authenticated callback tests, retry/dead-letter evidence |
| Vulnerability management | Verification required | Dependency scanning, container/image scanning, patch SLA and remediation records |
| Independent security test | Blocked on assessor | Scoped penetration test and closure of critical/high findings |
| Incident and breach response | External decision | Approved plan, contact tree, tabletop exercise and notification responsibilities |
| Retention and disposal | External decision | Agency/legal approval by data class and tested deletion/legal-hold procedures |

## Nationwide deployment controls

| Control | Current status | Required evidence before nationwide rollout |
| --- | --- | --- |
| Agency provisioning | Verification required | Repeatable onboarding/offboarding runbook and least-privilege administrator workflow |
| Capacity model | Verification required | Per-agency/user/case/evidence assumptions, peak targets and cost forecast |
| Load and soak testing | Verification required | Production-shaped PostgreSQL, API, queue, worker and object-storage results |
| Regional architecture | External decision | Primary/secondary region, recovery objectives, data-residency and failover decisions |
| Zero-downtime deployment | Verification required | Migration compatibility, rolling deployment and rollback exercise |
| Cross-agency exchange | Implemented; verification required | Legal-authority workflow, recipient validation, audit and revocation tests |
| Support operations | External decision | Service levels, escalation paths, after-hours coverage and agency communications |
| Configuration governance | Verification required | Versioned environment inventory, change approval and drift detection |

## HIPAA readiness evidence

| Requirement area | Current status | Required evidence |
| --- | --- | --- |
| Applicability and role determination | External decision | Counsel determination of covered-entity/business-associate roles and system boundary |
| Security risk analysis | Blocked on formal assessment | Documented asset/data-flow inventory, threats, likelihood, impact and risk register |
| Risk management | Verification required | Owners, remediation dates, accepted residual risks and periodic review process |
| Business associate agreements | External decision | BAAs with customers and every applicable subcontractor handling ePHI |
| Administrative safeguards | External decision | Workforce access, sanctions, training, contingency and evaluation policies |
| Physical safeguards | External decision | Hosting/provider evidence and workforce-device/facility procedures |
| Technical safeguards | Implemented in part | Access control, MFA, audit, integrity, authentication and transmission evidence |
| Breach notification | External decision | Contractual responsibilities, assessment workflow and notification procedures |
| Documentation retention | External decision | Six-year HIPAA documentation process where applicable |

## CJIS readiness evidence

| Requirement area | Current status | Required evidence |
| --- | --- | --- |
| CJIS applicability and CJI boundary | External decision | Participating agency and CJIS Systems Agency determination |
| CJIS v6.1 control mapping | Blocked on formal assessment | Applicable-control matrix with implementation statements and evidence links |
| Personnel and training | External decision | Screening, security awareness, role training and termination procedures |
| Identification and authentication | Implemented in part | Enforced MFA evidence, account lifecycle, privileged access and recovery approval |
| Encryption and cryptography | Verification required | CJIS-approved deployment design and cryptographic module/configuration evidence |
| Logging and accountability | Verification required | Event coverage, centralized protection, review procedures and retention approval |
| Incident response | External decision | CSA-aligned reporting contacts, playbooks and exercise results |
| Cloud/provider authorization | External decision | Agency/CSA review, contracts, data location and provider responsibility matrix |
| Mobile and remote access | Verification required | Device management, session controls, encryption and agency approval |

## Required release sign-offs

- Engineering owner: all implemented controls linked to reproducible evidence.
- Security owner: risk register and security testing accepted.
- Operations owner: deployment, monitoring, recovery and incident exercises passed.
- Privacy/legal owner: HIPAA applicability, BAAs, retention and breach duties approved.
- Participating agency and CJIS authority: CJI deployment and operating model approved.
- Product owner: remaining residual risks explicitly accepted before launch.
