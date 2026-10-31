# Beacon local development

These steps create a clean Windows development environment without placing
credentials in Git. Python 3.11 or 3.12, Node.js 20 or newer, PostgreSQL and
Redis are required. ClamAV is required when exercising evidence uploads.

## Backend

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Replace every placeholder in `.env` with local-only values. Never commit `.env`.
Create the configured PostgreSQL database, then initialize and verify its schema:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Start the durable worker in a
second activated terminal when testing queued operations:

```powershell
python scripts/run_worker.py
```

## Frontend

From `beaconsystems.client` in another PowerShell terminal:

```powershell
Copy-Item .env.example .env
npm ci
npm run dev
```

The example frontend environment points to the local API. Production builds must
set `VITE_API_BASE_URL` to the approved HTTPS API address, or leave it unset when
the API is served from the same origin.

## Visual Studio

Open `BeaconSystems.slnx`. In the Python Environments node, add the existing
environment at `.venv\Scripts\python.exe` and select **Make this the default
environment for new projects** if Visual Studio has not detected it automatically.
This machine-specific choice belongs to Visual Studio user settings and must not
be encoded as a developer-specific absolute path in the shared project file.

## Verification

Run the checks before opening a pull request:

```powershell
python -m ruff check .
python -m pytest
Set-Location beaconsystems.client
npm run lint
npm run build
```

For browser acceptance tests, install the supported browsers once with
`npm run test:e2e:install`, then run `npm run test:e2e`.

Before a production release, run the repeatable staging gate against the deployed
staging API (set `BEACON_LOAD_TEST_TOKEN` when testing protected paths):

```powershell
python scripts/run_staging_exercise.py --base-url https://staging.example.gov
```

The gate verifies schema drift, capacity-plan validity, repository hygiene, the
full backend suite, and bounded concurrent HTTP latency and error thresholds.
Use synthetic records only and retain the output with the release evidence.
