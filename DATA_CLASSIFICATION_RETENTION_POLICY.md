# Data classification and retention policy

Owner: Privacy Officer; approvals: Legal, Records Management, Security and agencies.

| Class | Examples | Minimum handling |
|---|---|---|
| Restricted | CJI, ePHI/medical, DNA/biometrics, minors/victims, credentials/keys | Need-to-know; encryption; audit; no production data in development; approved transfer |
| Confidential | Cases, evidence, alerts, leads, personnel and partner records | Tenant/role restriction; encryption; logged sharing |
| Internal | Metrics, procedures, non-public configuration | Authenticated workforce and controlled repositories |
| Public | Approved public alerts/contact data | Release approval, integrity and accessibility review |

The strictest applicable class controls a mixed record. Legal holds, court orders,
public-records law and agency schedules override routine deletion.

| Record | Proposed baseline | Required disposal evidence |
|---|---:|---|
| HIPAA/security policy and assessment evidence | At least 6 years after creation or last effective date | Approval and deletion record |
| Authentication/security audit records | 7 years from event | Signed deletion report |
| Cases, evidence and CJI | Agency schedule; never auto-delete before approval | Records authorization |
| Missing-person profiles/alerts | Agency schedule after resolution/closure | Hold check and deletion/anonymization report |
| Content-free operational metrics | 13 months | Monitoring report |
| Backups | 35 days absent hold/recovery exception | Vault expiry report |
| Incident/support records | 7 years after closure | Ticket report |

These are launch proposals, not universal legal conclusions. Before automation,
inventory all copies, attach jurisdiction rules, configure dual approval/dry run,
and verify disposal across primary storage, replicas, caches and backup expiry.
