# Encryption and key-management evidence

Owner: Security/KMS Administrator; independent review required.

| Control | Evidence | Status |
|---|---|---|
| TLS | Endpoint scan, policy, certificate owner/renewal | Pending deployment |
| Database/storage | Provider encryption and non-secret key ID | Pending deployment |
| Field encryption | Tests and production custody | Code implemented; custody pending |
| Audit HMAC | Key ID, rotation and verifier result | Code implemented; evidence pending |
| Backups/replicas | Encryption and restore proof | Pending exercise |
| Secret management | Inventory, access and rotation | Manifest exists; store pending |
| KMS/HSM resilience | Ownership, region, recovery, separation | Pending approval |

Never record secret values. Creation, activation, rotation, disablement and destruction
use approved tickets, auditable timestamps and two-person control for high-impact keys.
Compromise response isolates the key, revokes dependents, assesses re-encryption,
preserves evidence, notifies affected organizations and validates recovery.
