# BeaconSystems

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
