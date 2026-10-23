# Beacon operations and phase gates

## Phase II implemented controls

The durable queue supports retries, dead letters, tenant-scoped inspection,
audited manual replay, worker heartbeats, shutdown and configurable retention.
Failed handlers roll back uncommitted business writes before recording retries.
The Administration > Operations page shows bounded dead-letter results and health.

Authenticated monitoring systems can scrape `/operations/jobs/metrics/prometheus`.
Use a short-lived token for an authorized supervisor or administrator; agency
tokens receive agency-scoped queue values. Worker capacity is shared globally.
Metrics contain no job payloads or worker identities. Configure your monitoring
platform to alert when `beacon_queue_degraded` is 1 for five minutes or
`beacon_queue_dead_letters` is greater than 0. Monitor scrape failures separately.
An alert configuration in the monitoring platform is required; exporting metrics
alone does not send notifications.

When jobs fail, inspect dependencies and correct the cause before replaying.
Provide a meaningful replay reason. Observe the retry, and verify the business
result as well as the queue status. Never paste investigative payloads into logs.

## Phase II production acceptance still required

- Select and configure external delivery providers and authenticate their callbacks.
  The current delivery handler records in-app availability; it does not prove
  email, SMS, push, or external agency delivery.
- Configure monitoring scrapes, alert destinations and access-token rotation.
- Execute multi-worker, worker-kill, database-outage, slow-provider and rolling
  deployment exercises against an isolated PostgreSQL staging environment.
- Approve operational retention periods with participating agencies.

These external acceptance gates prevent claiming full production Phase II completion.
Local SQLite tests cannot establish PostgreSQL locking or outage behavior.

## Phase III investigator workflow

The investigator home view uses `/dashboard/investigator`. It returns at most
10 assigned active cases, 10 urgent active alerts and 10 pending case leads.
Cases require both the current agency and investigator assignment. Closed,
resolved and archived cases are excluded. Alerts also require the current
recipient agency. Pending leads are case leads, not individual assignments.
Priority cases appear first; leads appear oldest first. Each list reports
whether additional work exists. Team cases and temporary read grants remain
available through the existing authorized case browser.

The case profile now loads its protected timeline with the investigator session,
orders activity newest first, avoids duplicating sightings already represented
as timeline events, and audits manually created timeline entries.

Evidence intake now requires an authorized case selection, controlled evidence
category, collection time, sensitivity decision and retention policy. The API
validates those classifications and records them with the initial custody event.

Case leads now have accountable owners, controlled priorities and statuses, due
dates, closure resolutions and audited changes. Investigators see their own or
unassigned leads; assignment remains restricted to active users in the case
agency.

Generated matches now enter a tenant-scoped human review queue. Reviewers must
record a reason when confirming, rejecting or requesting more information;
Beacon stores the reviewer and time, audits the decision, and prevents an
investigator from silently changing a final outcome.

Investigator notifications are persisted per user and tenant rather than stored
in one browser. Alerts on assigned cases create an investigator notification;
opening it records a durable read timestamp and an audit event. Notification
lists are bounded by the shared pagination contract.

Mobile and accessibility safeguards now include keyboard skip navigation,
screen-reader route focus, visible focus indicators, reduced-motion and forced-
color support, 44-pixel mobile touch targets, and overflow-safe mobile content.
Case information uses a complete keyboard tab pattern with selected-state,
controlled-panel and arrow/Home/End navigation semantics. The investigator
workspace provides an explicit refresh action, persistent-notification feedback,
and labelled work queues.
The required real-device/browser sign-off matrix is documented in
`PHASE_III_MOBILE_ACCESSIBILITY_ACCEPTANCE.md`; Phase III is not accepted
until those staging checks are recorded and approved.

## Production identity assurance

Production startup now requires `MFA_ENFORCEMENT_ENABLED=true`. After a valid
password, an unenrolled user receives only a five-minute enrollment challenge;
Beacon does not create an application or refresh session until the authenticator
code is proven. Refresh sessions record whether MFA authenticated the session,
and pre-enforcement sessions cannot be refreshed or used after enforcement is
enabled. MFA cannot be disabled while the release gate is active.

Apply migration `3d6a02b9e841` before enabling this setting. Test enrollment with
designated break-glass administrators in staging, verify recovery procedures, and
then revoke all legacy sessions before production cutover.

## Production encryption gate

Production startup requires PostgreSQL certificate and hostname verification with
`sslmode=verify-full` and an approved `sslrootcert`. These may be supplied in
`DATABASE_URL`, or through `DB_SSLMODE` and `DB_SSLROOTCERT` when the URL is built
from the individual database settings. Rotate the trust bundle through the normal
configuration change process and test connectivity before removing the old CA.

The evidence bucket must block public access, enable versioning, and use the exact
configured customer-managed KMS key as its default encryption. The KMS key must be
a full ARN owned by the same AWS account as `OBJECT_STORAGE_EXPECTED_OWNER`.
Beacon also requests that key on every evidence upload and records encryption
metadata from the storage boundary, avoiding a separate flag that could report a
file as encrypted when it was not. Preserve the bucket, KMS policy, key-rotation,
database encryption, and encrypted-backup configuration as release evidence.

## Phase IV resilience and recovery

`/health` is a process liveness check. `/ready` verifies the database on every
request because Beacon cannot safely serve without its tenant boundary. Production
checks for the shared authentication limiter, evidence storage and malware scanner
are cached for `READINESS_DEPENDENCY_CACHE_SECONDS` (300 seconds by default).
Their failure returns `{"status":"degraded"}` with HTTP 200 so unaffected case
work can continue; the affected workflow still fails closed at its own boundary.
A database failure returns HTTP 503 and removes the instance from service.

Alert on both `not_ready` and `degraded`. Do not treat a degraded response as proof
that evidence uploads or authentication are usable. The implementation and required
recovery exercises are tracked in `PHASE_IV_RESILIENCE_RECOVERY.md`.

After restoring a production backup into an isolated PostgreSQL environment, set
only `BEACON_RESTORE_DATABASE_URL` for the restricted verification role and run:

```powershell
python scripts/verify_restored_database.py
```

The command refuses the configured application and migration database identities,
uses a read-only transaction, verifies the current Alembic head and required tables,
checks core relationships, and prints only table counts—not investigative records.
Save its JSON output with the timed restore evidence, then destroy the isolated
restore according to the approved data-handling procedure.
