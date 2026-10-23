# Phase IV production resilience and recovery

Phase IV prepares Beacon to remain safe and operable through dependency failures,
deployments and recoveries. Passing source tests is implementation evidence; it is
not proof that a cloud backup can be restored or that an incident team is ready.

## Implementation scope

- [x] Separate liveness from readiness.
- [x] Treat the database as the critical API readiness dependency.
- [x] Surface production storage, malware-scanner and authentication-limiter
  failures as degraded service without creating an all-instance outage.
- [x] Cache external readiness probes to limit nationwide health-check cost.
- [x] Add a non-destructive restored-database verification command.
- [x] Add backup, restore, rollback and incident-response runbooks.
- [x] Add recovery evidence templates with owners, timestamps, RPO and RTO results.
- [x] Add deployment shutdown and rollback verification contracts.
- [x] Complete secret inventory and rotation procedures.

## External acceptance gates

- Configure encrypted database backups and point-in-time recovery in the selected
  production platform.
- Restore a backup into an isolated environment and pass Beacon's verification
  command without using live user access.
- Measure and approve recovery point and recovery time objectives.
- Exercise an API rollout, worker rollout, rollback, dependency outage and regional
  recovery with named operational owners.
- Exercise secret and KMS-key rotation using the approved secret manager.
- Link logs, screenshots and approvals in the release evidence record.

Phase IV is code-complete only when every implementation item is checked. It is
production-accepted only when every external gate has dated evidence and approval.
