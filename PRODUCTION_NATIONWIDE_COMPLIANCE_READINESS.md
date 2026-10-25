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
| Key and secret management | Implemented in part; verification required | KMS ARN/account validation and rotation runbook implemented; access policy, secret-manager inventory, rotation exercise and break-glass evidence required |
| Audit integrity and retention | Implemented in part; verification required | Append-only tenant RLS and HMAC chains implemented; centralized immutable destination, scheduled verification, clock synchronization and approved retention required |
| Backups and recovery | Implemented in part; verification required | Read-only restore verifier and runbook implemented; encrypted backups, point-in-time recovery and successful timed restoration exercise required |
| High availability | Implemented in part; verification required | Cached dependency degradation and graceful shutdown implemented; multi-instance API/worker tests, load-balancer readiness and zone/region failure decision required |
| Monitoring and incident alerting | Implemented in part; verification required | Bounded API, dependency and queue metrics implemented; scrape configuration, alert destinations, on-call ownership and alert exercise required |
| External alert delivery | Blocked on provider selection | Provider contract, authenticated callback tests, retry/dead-letter evidence |
| Vulnerability management | Implemented in part; verification required | Dependency, image scanning and retained SBOMs implemented; patch SLA, triage and remediation records required |
| Independent security test | Blocked on assessor | Scoped penetration test and closure of critical/high findings |
| Incident and breach response | Implemented in part; verification required | Plan and tabletop package implemented; approved contact tree, exercise and notification responsibilities required |
| Retention and disposal | Implemented in part; external approval required | Classification, proposed schedule and legal-hold controls implemented; agency/legal approval and tested disposition required |

## Nationwide deployment controls

| Control | Current status | Required evidence before nationwide rollout |
| --- | --- | --- |
| Agency provisioning | Implemented in part; verification required | Audited creation, suspension/offboarding revocation and runbook implemented; approval, training and lifecycle exercise required |
| Capacity model | Implemented in part; verification required | Versioned provisional targets implemented; measured results, approved assumptions and cost forecast required |
| Load and soak testing | Verification required | Production-shaped PostgreSQL, API, queue, worker and object-storage results |
| Regional architecture | External decision prepared | Decision record implemented; primary/secondary region, recovery objectives, residency and failover approval required |
| Zero-downtime deployment | Implemented in part; verification required | Graceful API/worker shutdown and rollback runbook implemented; migration compatibility, rolling deployment and rollback exercise required |
| Cross-agency exchange | Implemented; verification required | Legal-authority workflow, recipient validation, audit and revocation tests |
| Support operations | External decision prepared | Decision record implemented; service levels, escalation, staffing and agency communications required |
| Configuration governance | Implemented in part; verification required | Versioned inventory, secret-safe validation and fingerprint implemented; deployment integration, change approval and drift-response exercise required |

## HIPAA readiness evidence

| Requirement area | Current status | Required evidence |
| --- | --- | --- |
| Applicability and role determination | External decision | Counsel determination of covered-entity/business-associate roles and system boundary |
| Security risk analysis | Implemented in part; external validation required | Risk register and data-flow inventory implemented; Security/Privacy validation and deployed-environment assessment required |
| Risk management | Verification required | Owners, remediation dates, accepted residual risks and periodic review process |
| Business associate agreements | External decision | BAAs with customers and every applicable subcontractor handling ePHI |
| Administrative safeguards | Implemented in part; external evidence required | Access, termination, screening, training, contingency and assessment policies implemented; approval and execution records required |
| Physical safeguards | External decision | Hosting/provider evidence and workforce-device/facility procedures |
| Technical safeguards | Implemented in part | Access control, MFA, audit, integrity, authentication and transmission evidence |
| Breach notification | External decision | Contractual responsibilities, assessment workflow and notification procedures |
| Documentation retention | External decision | Six-year HIPAA documentation process where applicable |

## CJIS readiness evidence

| Requirement area | Current status | Required evidence |
| --- | --- | --- |
| CJIS applicability and CJI boundary | External decision | Participating agency and CJIS Systems Agency determination |
| CJIS v6.1 control mapping | Implemented in part; CJIS ISO validation required | Family mapping implemented; requirement-level applicability, evidence and CSA approval required |
| Personnel and training | Implemented in part; external evidence required | Screening, awareness and termination procedures implemented; authorized screening/training records required |
| Identification and authentication | Implemented in part | Enforced MFA evidence, account lifecycle, privileged access and recovery approval |
| Encryption and cryptography | Verification required | CJIS-approved deployment design and cryptographic module/configuration evidence |
| Logging and accountability | Verification required | Event coverage, centralized protection, review procedures and retention approval |
| Incident response | Implemented in part; external validation required | Playbook and exercise packet implemented; CSA-aligned contacts and completed exercise required |
| Cloud/provider authorization | External decision | Agency/CSA review, contracts, data location and provider responsibility matrix |
| Mobile and remote access | Verification required | Device management, session controls, encryption and agency approval |

## Required release sign-offs

- Engineering owner: all implemented controls linked to reproducible evidence.
- Security owner: risk register and security testing accepted.
- Operations owner: deployment, monitoring, recovery and incident exercises passed.
- Privacy/legal owner: HIPAA applicability, BAAs, retention and breach duties approved.
- Participating agency and CJIS authority: CJI deployment and operating model approved.
- Product owner: remaining residual risks explicitly accepted before launch.
