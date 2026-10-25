# Data flow inventory

Complete deployment-specific destinations and vendors before production.

| Flow | Classification | Source → destination | Controls | Open evidence |
|---|---|---|---|---|
| Authentication/session | Restricted | Browser → API → database/limiter | TLS, MFA, hashing, expiry, revocation | Production TLS/IdP/Redis |
| Case/person/lead | Restricted/Confidential | Authorized user → API → database | Tenant RLS, role/case access, audit | Managed DB encryption/backup |
| Evidence upload | Restricted | Browser → API → scanner → object storage | Size/type checks, malware scan, KMS, tenant key | Provider/KMS exercise |
| Alerts/BOLO | Restricted/Public after approval | Supervisor → queue/provider/agencies | Approval, scope, retry, receipts, audit | Provider contract/callback test |
| Partner exchange | Restricted | Partner/agency → API → case | Authentication, legal authority, audit | Agreements and endpoint approval |
| Audit/metrics | Restricted/Internal | API/worker → log/monitoring platform | HMAC, minimization, bounded labels | Immutable destination/retention |
| Backup/recovery | Restricted | Database/storage → backup vault/restore | Encryption, access separation, verifier | Restore and disposal evidence |

No production data flows to developer devices, source control, browser-test fixtures,
analytics advertising platforms or unapproved support tools.
