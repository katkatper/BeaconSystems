# Nationwide Phase 0 Completion Record

Date: 2026-08-09

## Completed release gates

- Production startup rejects wildcard CORS, weak secrets, and runtime schema
  bootstrapping.
- Local schema helpers run only when explicitly enabled outside production.
- Duplicate API router registrations were removed.
- Database connections use bounded pooling, recycling, and health checks.
- Person, case, supervisor, legal, BOLO, partner-intake, external-record, and
  matching workflows enforce agency or authorized-case boundaries.
- Partner intake, external intelligence, and generated match records have
  explicit tenant keys with a backfill migration.
- Global integration configuration is system-admin only; agency users receive
  only active, approved sources.
- Matching is authenticated, tenant-scoped, role-restricted, and candidate
  bounded.
- Operational collection APIs publish a common bounded pagination contract via
  `X-Page-Limit`, `X-Page-Offset`, and `X-Has-More` headers.
- Frontend pages use the environment-configured API base instead of local hosts.
- Database-backed negative tests prove that Agency A cannot retrieve Agency B
  person or partner-intake records.
- Alembic branches are reconciled into the single `fe5f60718293` migration head.

## Verification required for every release

1. Run authorization and production-configuration unit tests.
2. Run database-backed tenant-isolation tests.
3. Confirm `alembic heads` returns exactly one head.
4. Import the FastAPI route modules with production schema bootstrap disabled.
5. Run frontend lint and the production build.

## Deployment prerequisites outside this repository

Phase 0 makes the application safe to proceed into scale engineering; it does
not by itself constitute nationwide production authorization. Before deployment:

- configure production secrets in a managed secret store;
- set explicit HTTPS `CORS_ORIGINS` and `VITE_API_BASE_URL` values;
- run Alembic as a controlled pre-deployment job;
- execute the tenant-key backfill against a sanitized production-sized copy and
  review any legacy rows whose `agency_id` remains null;
- complete an independent security and privacy assessment;
- add Phase 1 object storage, queueing, observability, backup, and load-testing
  infrastructure described in `docs/nationwide-readiness.md`.
