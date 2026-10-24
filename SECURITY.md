# Security and repository hygiene

## Credentials

- Never commit `.env` files or place them in source archives.
- Commit only sanitized `.env.example` templates with placeholder values.
- Treat credentials included in an archive, log, screenshot, or shared message as exposed. Rotate them at their issuing systems; deleting the archive does not revoke them.
- Keep production secrets in the deployment platform's secret manager.

## Repository contents

Do not commit or package installed dependencies, virtual environments, build output, caches, local uploads, evidence, or repository metadata. This includes `node_modules`, `.venv`, `venv`, `bin`, `obj`, `dist`, `uploads`, `__pycache__`, and `.git`.

Before committing or preparing a source package, run:

```powershell
python scripts/check_repository_hygiene.py
git status --short
```

Create source archives from tracked files instead of zipping the working directory:

```powershell
git archive --format=zip --output BeaconSystems-source.zip HEAD
```

The repository-hygiene workflow performs the tracked-file check on every push and pull request.

## Automated security checks

The production release-gates workflow blocks a pull request or `master` build
when backend tests, source analysis, or dependency audits fail. Bandit scans the
Python application for medium- and high-severity findings, `pip-audit` checks
the pinned production dependencies, and `npm audit` checks frontend production
dependencies at moderate severity or higher.

The same gate builds the API and worker images, creates CycloneDX JSON software
bills of materials for both, retains them as build evidence, and blocks on fixed
high or critical image vulnerabilities reported by Trivy. Unfixed findings remain
visible for risk triage; the security owner must track them under the approved
patch and residual-risk process rather than silently suppressing individual results.

The Python audit narrowly ignores `PYSEC-2026-1325` because it affects ECDSA
operations in the transitive `ecdsa` package, while Beacon explicitly signs and
verifies tokens with HMAC SHA-256 (`HS256`). The advisory currently has no fixed
release. Remove this exception if Beacon adopts an ECDSA algorithm, if a fixed
dependency path becomes available, or if the authentication implementation
changes. Do not add broad audit exclusions.

## Audit records

Beacon audit rows are tenant-scoped with PostgreSQL Row-Level Security and are
append-only: application operations cannot update or delete an existing audit
event. Each committed event is also emitted as sanitized JSON through the
`beacon.security.audit` logger for collection by the production log router.
Configure the deployment platform to retain that stream in approved centralized
storage; the application intentionally excludes free-form event details from the
external stream to reduce disclosure risk.

New audit events also form an agency-scoped HMAC-SHA256 chain. Production requires
a dedicated `AUDIT_INTEGRITY_KEY` and non-secret `AUDIT_INTEGRITY_KEY_ID`.
PostgreSQL advisory transaction locks serialize each agency's chain head across API
instances. Pre-migration events remain explicitly counted as unsigned; Beacon does
not misrepresent them as cryptographically verified.

Use an approved read-only audit replica or scoped audit role to run:

```powershell
$env:BEACON_AUDIT_DATABASE_URL = "postgresql+psycopg2://..."
$env:AUDIT_INTEGRITY_KEYS_JSON = '{"audit-2026-v1":"..."}'
python scripts/verify_audit_integrity.py
```

Keep every retained key version available for the corresponding audit-retention
period. The verifier streams rows, emits only validity and counts, and never emits
event contents or key values. A failed chain is a security incident; preserve the
database and centralized log copy before investigation.

## Production evidence encryption

Production object storage requires a customer-managed AWS KMS key. Every Beacon
upload explicitly requests `aws:kms` encryption with that key and identifies the
expected twelve-digit AWS account owner for the bucket. Apply a bucket policy
that denies unencrypted writes, denies writes using a different KMS key, and
blocks access from principals outside the approved deployment roles.

The evidence bucket must enable all four Amazon S3 public-access-block settings
and bucket versioning. Beacon verifies both controls during production startup.
Versioning supports recovery from accidental overwrite or deletion; retention
and lifecycle rules must still be selected through the applicable records and
legal-hold policies.

Beacon validates access to the expected S3 bucket and connectivity to the
shared Redis authentication limiter during production startup. These checks use
bounded connection timeouts. If either dependency is unavailable or points to
the wrong AWS account, the instance fails startup and must not receive traffic.

## PostgreSQL tenant isolation

Authenticated requests attach `beacon.agency_id` and `beacon.platform_admin`
to each database transaction. Row Level Security policies use those settings as
a second tenant boundary beneath application authorization.

Production must use separate database roles:

- A migration owner that owns schema objects and runs Alembic.
- A restricted application role that is not a superuser, does not own protected
  tables, and does not have `BYPASSRLS`.

Do not grant the application role ownership or `BYPASSRLS`; either would bypass
the tenant policies. Automated partner ingestion must establish its destination
agency context before accessing tenant-protected records.

Set `DATABASE_URL` to the restricted application role. Supply
`MIGRATION_DATABASE_URL` only to Alembic or the deployment migration job. Beacon
validates the runtime role and all required tenant policies during production
startup and refuses to serve traffic when the database posture is unsafe.

## Case access codes

Code-based case access has no built-in or demonstration fallback. Store
`BEACON_CASE_ACCESS_CODE` in the deployment secret manager and use a randomly
generated value of at least 16 characters. Beacon refuses production startup
when it is missing or too short. Rotate the code after suspected disclosure and
review the corresponding case-access audit events.
