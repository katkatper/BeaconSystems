# BeaconSystems

Local development setup is documented in [DEVELOPMENT.md](DEVELOPMENT.md).

## Phase I capacity gate

Run the API against a production-like database and shared object-storage stack,
then execute the bounded load gate:

```powershell
$env:BEACON_LOAD_TEST_TOKEN = "short-lived-test-token"
python scripts/load_test_phase_one.py --base-url https://beacon.example.gov `
  --path health --path ready --path "evidence/?limit=50" `
  --requests 10000 --concurrency 100 --max-p95-ms 750 --max-error-rate 0.01
```

The command returns a nonzero exit status when latency or error thresholds are
missed and emits a single JSON summary suitable for CI evidence. Never use
production user credentials or live investigative records for load testing.

Production uploads require shared S3 storage and ClamAV. API instances contain
no durable upload state; files are scanned before storage and accessed through
tenant-scoped object keys and short-lived signed URLs.

## Phase II worker

Build and run the durable operations worker separately from the API:

```powershell
docker build --file Dockerfile.worker --tag beacon-worker:local .
docker run --env-file .env beacon-worker:local
```

The worker uses PostgreSQL for durable jobs and tenant isolation. Deploy at
least two worker replicas for production availability. `SIGTERM` stops new job
claims, allows the current handler to finish, records a final heartbeat, and
then exits. Monitor `/operations/jobs/metrics` for backlog, dead letters, and
active worker counts.

Completed jobs are retained for 30 days, dead-letter jobs for 180 days, and
inactive worker heartbeats for 7 days by default. The worker prunes expired
operational history every five minutes. Override the corresponding retention
environment variables only in accordance with agency audit and records policy;
queued, retrying, and running work is never removed by maintenance.

See [OPERATIONS.md](OPERATIONS.md) for the operations page, metrics export,
Phase II acceptance gates, Phase III investigator scope and Phase IV resilience
behavior. Phase IV implementation and external recovery gates are tracked in
[PHASE_IV_RESILIENCE_RECOVERY.md](PHASE_IV_RESILIENCE_RECOVERY.md).
