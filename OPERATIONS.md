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

Remaining Phase III slices: case timeline/profile improvements, evidence upload
and classification flow, lead ownership/status, match disposition, investigator
notifications/read receipts, and mobile/accessibility browser acceptance.
