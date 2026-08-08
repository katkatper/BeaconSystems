# Beacon Nationwide Readiness Program

## Objective

Prepare Beacon to expand from an initial controlled launch to multi-agency,
multi-state operation without weakening privacy, availability, auditability, or
investigative need-to-know controls.

Nationwide readiness is a release program, not a single deployment setting. A
larger record count does not increase the browser bundle; it increases pressure
on tenant isolation, APIs, databases, storage, queues, and operations.

## Current assessment

Beacon already has several useful foundations:

- agency identifiers on core operational records;
- case-level authorization helpers and supervisor role enforcement;
- Alembic migrations;
- S3 integration scaffolding;
- an audit/activity model;
- route-level frontend code splitting;
- environment-based database credentials.

The following items are nationwide launch blockers:

1. Tenant isolation is not yet uniformly enforced. Some older list and matching
   routes still query entire tables, and not every agency-owned model has an
   explicit non-null `agency_id`.
2. The API currently allows every CORS origin.
3. Application startup calls `create_all` and local schema maintenance, including
   duplicate startup calls. Production schema changes must run only through a
   controlled migration job.
4. Several APIs return full result sets. Large registries must use bounded,
   deterministic pagination.
5. Many frontend requests contain a hard-coded local API address rather than the
   configured API client.
6. Operational work such as alert distribution, matching, geocoding, report
   generation, and partner ingestion runs without a durable distributed queue.
7. There is no documented nationwide availability target, regional failover
   procedure, backup recovery objective, or production telemetry standard.
8. Uploaded person photos still use local disk before association with a record;
   nationwide deployment requires encrypted object storage, malware scanning,
   signed access, retention rules, and immutable evidence handling where
   applicable.

## Required architecture boundaries

### Tenant and jurisdiction isolation

- Every agency-owned table must carry a non-null agency or tenant identifier.
- Authorization must be applied in a shared repository/service layer, not
  independently re-created by each route.
- Cross-agency access must use explicit, expiring, audited grants.
- Database row-level security should provide a second enforcement layer for
  sensitive production tables.
- Automated tests must attempt cross-agency reads and writes for every resource.

### API scale

- All collection endpoints must enforce page-size limits and stable ordering.
- Prefer cursor pagination for high-volume event, alert, evidence, and audit
  tables; offset pagination is acceptable for small administrative registries.
- Expensive searches must be asynchronous or backed by a search index.
- Requests require timeouts, idempotency keys for important mutations, rate
  limits, and correlation identifiers.
- Publish and version an API contract before external agency integrations begin.

### Data platform

- Use managed PostgreSQL with connection pooling, encryption, automated backups,
  point-in-time recovery, read replicas, and tested regional restoration.
- Index agency ID together with common status, case, and timestamp filters.
- Partition very large append-only tables such as audit, alert delivery, and
  event history by time and/or tenant strategy validated with production-like
  load tests.
- Separate transactional data, search, analytics, and immutable audit workloads.

### Files and evidence

- Store files in encrypted object storage; application servers remain stateless.
- Use tenant-scoped object keys and short-lived signed URLs.
- Scan uploads, validate content independently of extensions, and record hashes.
- Apply legal hold, retention, deletion, and chain-of-custody policies by
  jurisdiction and evidence class.

### Distributed operations

- Introduce a durable queue for alert fan-out, read receipts, partner ingestion,
  matching, geocoding, exports, and notifications.
- Workers must support retry policies, dead-letter queues, idempotency, and an
  operator-visible failure console.
- Cache only data with explicit tenant-aware keys and safe invalidation rules.

### Availability and observability

- Define service-level objectives for API availability, alert delivery latency,
  recovery time, and recovery point.
- Centralize structured logs, metrics, traces, security events, and audit events.
- Alert on elevated authorization failures, cross-tenant test failures, queue
  backlog, database saturation, and alert-delivery degradation.
- Run load, failover, backup-restore, and incident-response exercises before
  multi-state expansion.

### National and international policy readiness

- Model jurisdiction, time zone, locale, measurement system, and retention policy
  explicitly instead of inferring them from an agency name or server location.
- Nationwide release requires state-specific retention and disclosure controls.
- International expansion additionally requires data-residency regions,
  cross-border transfer controls, localization, and country-specific legal review.

## Delivery roadmap

### Phase 0 — Release gates and security foundation

- Inventory every route and table for tenant ownership.
- Close all cross-agency read/write gaps and add negative authorization tests.
- Restrict CORS and validate all production configuration at startup.
- remove runtime schema mutation from production;
- replace hard-coded client API addresses;
- define production secrets, key rotation, MFA, session, and incident policies.

Exit gate: no critical cross-tenant findings, migrations are the only production
schema mechanism, and security tests run in continuous integration.

### Phase 1 — Bounded APIs and stateless storage

- Add standardized pagination envelopes and cursor support.
- Add required compound indexes and query-duration telemetry.
- Move all uploads to encrypted object storage with signed access.
- Add request IDs, structured logging, health/readiness checks, and API timeouts.

Exit gate: production-like datasets remain within agreed latency and memory
budgets, and application instances contain no durable local state.

### Phase 2 — Durable asynchronous operations

- Deploy the queue and workers.
- Move alert delivery, receipts, integrations, reports, matching, and geocoding
  behind idempotent jobs.
- Add retries, dead-letter handling, backlog dashboards, and replay controls.

Exit gate: worker or partner failures cannot lose alerts or block API capacity.

### Phase 3 — Multi-region resilience

- Deploy multiple availability zones, autoscaling, managed database failover,
  CDN delivery, and tested backup restoration.
- Establish a second-region recovery environment and run failover exercises.
- Complete independent penetration, privacy, and architecture reviews.

Exit gate: recovery objectives and peak-load targets are demonstrated, not only
documented.

### Phase 4 — Controlled national expansion

- Onboard agencies in cohorts with data migration validation and operational
  training.
- Monitor per-tenant capacity, delivery latency, support load, and policy drift.
- Expand regions only after the prior cohort meets its reliability gates.

## Immediate engineering sequence

The first implementation sprint should proceed in this order:

1. Build a route/table tenant-ownership matrix and automated cross-agency tests.
2. Centralize production configuration, restrict CORS, and disable production
   schema bootstrapping.
3. Replace hard-coded frontend API addresses with the shared API client.
4. Standardize pagination and add indexes to the highest-volume collections.
5. Move person photos and evidence files to tenant-scoped object storage.

No nationwide launch date should be committed until the Phase 0 and Phase 1 exit
gates pass against production-like data and an independent security review.
