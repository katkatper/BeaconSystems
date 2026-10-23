# Deployment and rollback runbook

## Before deployment

- Link the approved commit, image digest, migration plan and rollback decision.
- Confirm the release-gate workflow, database backup status and capacity headroom.
- Classify migrations as backward-compatible or release-blocking.
- Confirm `/health`, `/ready`, queue metrics and alert destinations are monitored.
- Set the platform termination grace period longer than
  `API_GRACEFUL_SHUTDOWN_SECONDS` and the worker lease/handler completion window.

## Rolling deployment

1. Run backward-compatible migrations from the restricted migration job.
2. Deploy one API canary and verify liveness, readiness, authentication, tenant
   isolation, a read-only case flow and logs.
3. Roll API instances gradually. `SIGTERM` stops the process after Uvicorn's
   graceful window; Beacon disposes its database pool during shutdown.
4. Roll workers separately. Confirm the old worker records its final heartbeat and
   claimed jobs finish or become safely reclaimable after their lease.
5. Verify queue backlog, dead letters, error rate and dependency degradation.

## Rollback

1. Stop rollout and preserve the failing image, logs and request identifiers.
2. Roll back application images only when the current database schema is compatible.
3. Do not downgrade destructive migrations. Use a forward repair or restore only
   under the approved recovery process.
4. Verify tenant access, authentication, evidence retrieval and queue processing.
5. Record timeline, customer impact, decision owner and follow-up actions.
