# Production-like staging validation

The Compose stack is an isolated validation environment, not a production design.
Production requires managed TLS, KMS-backed object storage, TLS Redis, immutable
logging, managed backups, network controls and approved secrets.

## Start safely

1. Copy `config/staging.env.example` to the gitignored `config/staging.env`.
2. Replace every `CHANGE_ME` with generated staging-only values. Use a URL-safe
   database password and set `BEACON_STAGING_DB_PASSWORD` to the same value.
3. Set `BEACON_STAGING_API_URL` when the browser cannot reach `localhost:8000`.
4. Validate with `docker compose -f compose.staging.yml config --quiet`.
5. Build and start with `docker compose -f compose.staging.yml up --build`.
6. Confirm API `/health`, `/ready`, frontend port 8080, worker heartbeat, malware
   scan, Redis limiting and one Alembic head.

Use synthetic data only. Execute the role UAT and production acceptance exercise
packet; capture redacted evidence outside Git. Stop the stack normally. Destruction
of its named volumes requires explicit approval because it permanently deletes the
staging database and evidence.

The local-storage evidence backend is intentional for an isolated workstation
exercise and cannot satisfy production encryption evidence. A cloud staging
deployment must use the same managed services and controls planned for production.
