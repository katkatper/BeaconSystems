# Beacon security risk assessment

Owner: Security Officer (assign before production)  
Cadence: quarterly and after material architecture, regulatory or threat changes  
Scope: API, client, worker, database, storage, integrations, tenants and operations.

Likelihood and impact are scored 1–5; risk is their product: low 1–4, moderate
5–9, high 10–16, critical 17–25. Deployment owners must validate the scores.

| ID | Risk | Inherent | Existing controls | Required evidence/treatment | Target |
|---|---|---:|---|---|---:|
| R-01 | Cross-agency CJI/PII disclosure | 20 | Tenant queries, authorization tests, sessions | Independent staging isolation test | 5 |
| R-02 | Stolen credentials/session | 20 | MFA, rate limits, expiry/revocation | IdP evidence and abuse-alert exercise | 6 |
| R-03 | Privileged misuse | 16 | Roles, audit, access requests | Quarterly access review and immutable monitoring | 6 |
| R-04 | Audit alteration/deletion | 20 | HMAC chain and verifier | Immutable external copy and verifier exercise | 5 |
| R-05 | Ransomware/destructive event | 20 | Recovery procedures | Isolated restore and regional exercise | 8 |
| R-06 | Malicious sensitive upload | 16 | File validation/authentication | Malware quarantine evidence | 6 |
| R-07 | Vulnerable dependency/image | 16 | SBOM and blocking scans | Patch SLA and monthly review | 6 |
| R-08 | Key compromise | 20 | Rotation procedures | Managed KMS/HSM and dual-control evidence | 5 |
| R-09 | Vendor breach | 16 | Vendor review gate | Signed terms, BAA if applicable, annual review | 6 |
| R-10 | Unauthorized international transfer | 20 | Launch gate | Counsel-approved jurisdiction mechanism | 5 |
| R-11 | Nationwide outage/capacity failure | 20 | Health, retry, metrics | Load/failover tests and thresholds | 8 |
| R-12 | Improper retention/legal hold | 16 | Policy and audit | Retention jobs, hold and deletion proof | 6 |
| R-13 | Workforce error/social engineering | 16 | Least privilege/logging | Screening and annual exercises | 8 |
| R-14 | Incorrect automated correlation | 15 | Human review/confidence | Quality review and adverse-event process | 6 |

Security, Privacy, Operations and the Executive Risk Owner must sign and date
residual-risk decisions. HHS OCR treats risk analysis as an ongoing process and
requires risks to confidentiality, integrity and availability to be documented.
