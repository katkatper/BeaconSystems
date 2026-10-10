# Beacon engineering quality standard

Beacon is intended for sensitive, multi-agency investigations. A feature is not
production-ready merely because it works on a developer computer. Changes must
provide evidence for correctness, readability, maintainability, scalability,
security, efficiency, reliability, and testability.

## Required evidence

| Quality characteristic | Required engineering evidence |
| --- | --- |
| Correctness | Acceptance criteria, behavioral tests, validated inputs and outputs, and one Alembic migration head. |
| Readability | Clear domain names, small focused functions, consistent formatting, and comments that explain decisions rather than restate code. |
| Maintainability | Shared services for repeated behavior, stable interfaces, documented configuration, and no unrelated changes in a feature patch. |
| Scalability | Pagination and bounded queries, database indexes supported by query evidence, stateless API instances, shared rate limiting, and measured load tests before launch. |
| Security | Tenant authorization and database row-level security, least privilege, protected secrets, dependency and source scans, audit records, and threat review for sensitive changes. |
| Efficiency | Bounded network calls, pooled database connections, no avoidable full-table or unbounded API reads, and lifecycle rules for cloud storage. |
| Reliability | Explicit timeouts, narrow exception handling, safe failure behavior, health checks, observable errors, backups, and tested recovery procedures. |
| Testability | Deterministic unit, integration, authorization, tenant-isolation, migration, and end-to-end tests running in continuous integration. |

## Definition of done

A production-bound change must:

1. State the user or operational requirement it satisfies.
2. Include automated tests for normal, denied, invalid, and dependency-failure paths where applicable.
3. Preserve tenant isolation and auditability for every data path.
4. Avoid unbounded database queries, uploads, retries, and network calls.
5. Pass backend tests, the coverage floor, Ruff, Bandit, dependency audits,
   frontend lint, and the production frontend and container builds.
6. Include a reversible database migration when persistent data changes.
7. Update operational or security documentation when behavior or configuration changes.
8. Receive human review before production deployment.

## Technical-debt rules

- Do not introduce unexplained duplicated business or authorization logic.
- Do not leave placeholders, silent exception handlers, or temporary bypasses in
  a production path.
- Record intentional debt with an owner, risk, target date, and removal test.
- Prefer small refactors protected by tests over broad mechanical rewrites.
- Raise quality thresholds as debt is removed; never lower a gate merely to make
  a build pass.

## Current measured baseline

As of October 10, 2026, the backend suite has 141 passing tests plus seven
parameterized subtests and approximately 25.0 percent statement coverage across
the measured Python application packages. This is a floor, not a production
target. Most API routes still lack behavioral execution coverage.

The largest modules also exceed normal review-friendly size, including several
route modules and React pages over 700 lines. They should be split by domain as
behavioral tests are added. Refactoring them without tests would increase risk.

Before nationwide production launch, Beacon must add representative API and
browser end-to-end tests, multi-tenant concurrency and load tests, database
query-plan review for high-volume endpoints, and backup/restore and dependency-
failure exercises. Coverage must be raised progressively, prioritizing
authentication, authorization, tenant isolation, evidence, legal access, audit,
and partner-ingestion paths rather than chasing a percentage alone.
