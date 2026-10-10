# Legacy migration archive

These revisions record Beacon's pre-baseline schema history. They are retained
for audit and troubleshooting purposes, but they are not part of Alembic's
active `migrations/versions` path and must not be configured as a version
location.

Fresh environments start with revision `601d95116833` and then apply the
database security controls in revision `f2cc04888254`.

Existing environments must be backed up, reconciled with the baseline schema,
and explicitly stamped to the new head. Never run the baseline's table-creation
steps against an existing populated database.
