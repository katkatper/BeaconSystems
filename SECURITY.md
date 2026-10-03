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

## Audit records

Beacon audit rows are tenant-scoped with PostgreSQL Row-Level Security and are
append-only: application operations cannot update or delete an existing audit
event. Each committed event is also emitted as sanitized JSON through the
`beacon.security.audit` logger for collection by the production log router.
Configure the deployment platform to retain that stream in approved centralized
storage; the application intentionally excludes free-form event details from the
external stream to reduce disclosure risk.

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
