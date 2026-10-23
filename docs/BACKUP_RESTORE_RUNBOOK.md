# Backup and restore runbook

## Purpose and ownership

Use this runbook only in an approved isolated recovery environment. The operations
owner coordinates the exercise; the security owner approves access; the database
owner performs the restore; the application owner verifies Beacon. Never restore
production data onto a developer workstation or an internet-accessible database.

## Preconditions

- Approved incident or scheduled exercise identifier.
- Named operators and independent reviewer.
- Encrypted backup and KMS keys available through approved roles.
- Isolated network, private DNS and restricted PostgreSQL verification role.
- Destination storage encrypted and governed by the same retention requirements.
- Target RPO and RTO recorded before work begins.

## Restore procedure

1. Record the selected backup timestamp and expected recovery point.
2. Restore into a new isolated database; never overwrite the live database.
3. Apply network controls before allowing any client connection.
4. Create a read-only verifier credential through the secret manager.
5. Set `BEACON_RESTORE_DATABASE_URL` only in the verifier process. Keep
   `DATABASE_URL` and `MIGRATION_DATABASE_URL` pointed at their normal targets so
   the safety lock can detect accidental reuse.
6. Run `python scripts/verify_restored_database.py` and retain its JSON output.
7. If the restored revision is behind, record that fact before running migrations.
   Test migrations with the migration role, then rerun verification.
8. Perform approved application smoke tests with non-production operator accounts.
9. Record completion time, measured RPO/RTO, defects and reviewer decision.
10. Revoke temporary credentials and securely destroy the isolated restore when
    retention of the exercise environment is no longer authorized.

## Failure and escalation

Stop if the verifier identifies the live target, required tables are absent, the
migration revision differs unexpectedly, relationship checks fail, KMS access is
missing, or isolation cannot be demonstrated. Do not repair production records as
part of a restore drill. Preserve logs, notify the incident/release owner, and open
a tracked remediation with an owner and due date.
