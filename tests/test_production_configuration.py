import ast
import unittest
from pathlib import Path

from database.security_posture import database_role_violations

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ProductionConfigurationTests(unittest.TestCase):
    def test_main_has_no_wildcard_cors_or_unconditional_schema_bootstrap(self):
        source = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)

        self.assertNotIn('allow_origins=["*"]', source)
        self.assertNotIn("Base.metadata.create_all(bind=engine)",source, )
        self.assertEqual(source.count("app.include_router(person_router)"), 1)
        self.assertEqual(source.count("app.include_router(alerts_router)"), 1)
        self.assertEqual(source.count("app.include_router(sightings_router)"), 1)

    def test_production_settings_reject_unsafe_defaults(self):
        source = (REPOSITORY_ROOT / "config" / "settings.py").read_text(
            encoding="utf-8"
        )
        ast.parse(source)

        self.assertIn("validate_runtime_settings", source)
        self.assertIn("CORS_ORIGINS cannot contain '*' in production", source)
        self.assertIn(
            "CORS_ORIGINS entries must be HTTPS origins without paths in production",
            source,
        )
        self.assertIn("ENABLE_LOCAL_SCHEMA_BOOTSTRAP must be false", source)
        self.assertIn("SECRET_KEY must contain at least 32 characters", source)
        self.assertIn("AUDIT_INTEGRITY_KEY must contain at least 32 characters", source)
        self.assertIn("AUDIT_INTEGRITY_KEY_ID is required in production", source)
        self.assertIn("BEACON_CASE_ACCESS_CODE must contain at least 16 characters", source)
        self.assertIn("JWT_ISSUER is required in production", source)
        self.assertIn("JWT_AUDIENCE is required in production", source)
        self.assertIn("TRUSTED_HOSTS must list approved production hostnames", source)
        self.assertIn("TRUSTED_HOSTS cannot contain '*' in production", source)
        self.assertIn("HSTS_MAX_AGE_SECONDS must be at least 31536000", source)
        self.assertIn("OBJECT_STORAGE_KMS_KEY_ID is required in production", source)
        self.assertIn("RATE_LIMIT_REDIS_TIMEOUT_SECONDS must be greater than zero", source)
        self.assertIn("EXTERNAL_API_TIMEOUT_SECONDS must be greater than zero", source)
        self.assertIn("ARCGIS_GEOCODE_URL must use HTTPS in production", source)
        self.assertIn("MFA_SECRET_ENCRYPTION_KEY is required in production", source)
        self.assertIn("MFA_SECRET_ENCRYPTION_KEY must be a valid Fernet key", source)
        self.assertIn("MFA_ENFORCEMENT_ENABLED must be true in production", source)
        self.assertIn("READINESS_DEPENDENCY_CACHE_SECONDS must be greater than zero", source)
        self.assertIn("API_GRACEFUL_SHUTDOWN_SECONDS must be greater than zero", source)
        self.assertIn("Production database connections must use sslmode=verify-full", source)
        self.assertIn("Production database connections must specify sslrootcert", source)
        self.assertIn("OBJECT_STORAGE_KMS_KEY_ID must be a full KMS key ARN", source)
        self.assertIn(
            "OBJECT_STORAGE_KMS_KEY_ID account must match OBJECT_STORAGE_EXPECTED_OWNER",
            source,
        )

    def test_api_perimeter_has_security_headers_and_bounded_cors(self):
        main_source = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        middleware_source = (
            REPOSITORY_ROOT / "security" / "http_middleware.py"
        ).read_text(encoding="utf-8")

        self.assertIn("TrustedHostMiddleware", main_source)
        self.assertIn('docs_url=None if IS_PRODUCTION else "/docs"', main_source)
        self.assertNotIn('allow_methods=["*"]', main_source)
        self.assertNotIn('allow_headers=["*"]', main_source)
        for header in [
            "Cache-Control",
            "Content-Security-Policy",
            "Permissions-Policy",
            "Referrer-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
        ]:
            self.assertIn(header, middleware_source)

    def test_database_pool_uses_health_checks_and_bounded_capacity(self):
        source = (REPOSITORY_ROOT / "database" / "connection.py").read_text(
            encoding="utf-8"
        )
        ast.parse(source)

        self.assertIn("pool_pre_ping=True", source)
        self.assertIn("pool_size=DATABASE_POOL_SIZE", source)
        self.assertIn("max_overflow=DATABASE_MAX_OVERFLOW", source)
        self.assertIn('"slow_database_query"', source)
        self.assertIn('"sslmode": db_sslmode', source)
        self.assertIn('"sslrootcert": db_sslrootcert', source)

    def test_evidence_encryption_metadata_comes_from_storage_boundary(self):
        evidence_source = (
            REPOSITORY_ROOT / "routes" / "evidence_routes.py"
        ).read_text(encoding="utf-8")
        storage_source = (
            REPOSITORY_ROOT / "services" / "object_storage.py"
        ).read_text(encoding="utf-8")

        self.assertIn("is_encrypted=object_storage.is_encrypted", evidence_source)
        self.assertIn("encryption_key_id=object_storage.encryption_key_id", evidence_source)
        self.assertIn("get_bucket_encryption", storage_source)
        self.assertIn("Production evidence bucket default encryption", storage_source)

    def test_production_database_role_rejects_rls_bypasses(self):
        violations = database_role_violations(
            is_superuser=True,
            bypasses_rls=True,
            owned_tables=["cases"],
            unprotected_tables=["alerts"],
        )

        self.assertEqual(len(violations), 4)
        self.assertTrue(any("superuser" in item for item in violations))
        self.assertTrue(any("BYPASSRLS" in item for item in violations))
        self.assertTrue(any("cases" in item for item in violations))
        self.assertTrue(any("alerts" in item for item in violations))

    def test_alembic_uses_a_separate_migration_database_url(self):
        migration_environment = (
            REPOSITORY_ROOT / "migrations" / "env.py"
        ).read_text(encoding="utf-8-sig")
        example_environment = (
            REPOSITORY_ROOT / ".env.example"
        ).read_text(encoding="utf-8-sig")

        self.assertIn("MIGRATION_DATABASE_URL", migration_environment)
        self.assertIn("MIGRATION_DATABASE_URL", example_environment)

    def test_frontend_pages_do_not_hard_code_a_local_api_host(self):
        pages_directory = REPOSITORY_ROOT / "beaconsystems.client" / "src" / "pages"

        offenders = [
            path.name
            for path in pages_directory.glob("*.jsx")
            if "http://127.0.0.1:8000" in path.read_text(encoding="utf-8")
            or "http://localhost" in path.read_text(encoding="utf-8")
        ]

        self.assertEqual(offenders, [])

    def test_production_migrations_have_one_linear_head(self):
        baseline = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "601d95116833_create_beacon_production_baseline.py"
        ).read_text(encoding="utf-8")
        security = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "f2cc04888254_apply_beacon_database_security_controls.py"
        ).read_text(encoding="utf-8")

        self.assertIn("down_revision: Union[str, Sequence[str], None] = None", baseline)
        self.assertIn("down_revision: Union[str, Sequence[str], None] = '601d95116833'", security)

    def test_release_readiness_register_keeps_external_gates_visible(self):
        register = (
            REPOSITORY_ROOT / "PRODUCTION_NATIONWIDE_COMPLIANCE_READINESS.md"
        ).read_text(encoding="utf-8")

        self.assertIn("## Release-blocking controls", register)
        self.assertIn("## Nationwide deployment controls", register)
        self.assertIn("## HIPAA readiness evidence", register)
        self.assertIn("## CJIS readiness evidence", register)
        self.assertIn("not a representation that Beacon is", register)

    def test_phase_four_keeps_external_recovery_evidence_visible(self):
        phase_four = (
            REPOSITORY_ROOT / "PHASE_IV_RESILIENCE_RECOVERY.md"
        ).read_text(encoding="utf-8")

        self.assertIn("restored-database verification", phase_four)
        self.assertIn("recovery point", phase_four)
        self.assertIn("recovery time", phase_four)
        self.assertIn("external gate has dated evidence", phase_four)

        api_start = (
            REPOSITORY_ROOT / "scripts" / "start_production.py"
        ).read_text(encoding="utf-8")
        main = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("timeout_graceful_shutdown", api_start)
        self.assertIn("engine.dispose()", main)
        self.assertIn("STOPSIGNAL SIGTERM", dockerfile)

        for document in (
            "BACKUP_RESTORE_RUNBOOK.md",
            "DEPLOYMENT_ROLLBACK_RUNBOOK.md",
            "INCIDENT_RESPONSE_RUNBOOK.md",
            "SECRET_ROTATION_RUNBOOK.md",
        ):
            self.assertTrue((REPOSITORY_ROOT / "docs" / document).is_file())

    def test_phase_five_assurance_artifacts_remain_release_gates(self):
        phase_five = (
            REPOSITORY_ROOT / "PHASE_V_OPERATIONAL_ASSURANCE.md"
        ).read_text(encoding="utf-8")
        evidence = (
            REPOSITORY_ROOT / "PHASE_V_ASSURANCE_EVIDENCE_TEMPLATE.md"
        ).read_text(encoding="utf-8")
        lifecycle = (
            REPOSITORY_ROOT / "docs" / "AGENCY_LIFECYCLE_RUNBOOK.md"
        ).read_text(encoding="utf-8")

        assert "- [ ]" not in phase_five.split("## External acceptance gates")[0]
        assert "Central immutable log destination" in evidence
        assert "does not delete investigative records" in lifecycle

    def test_phase_six_governance_artifacts_remain_visible(self):
        required = (
            "PHASE_VI_COMPLIANCE_PRODUCT_READINESS.md",
            "SECURITY_RISK_ASSESSMENT.md",
            "DATA_CLASSIFICATION_RETENTION_POLICY.md",
            "INCIDENT_RESPONSE_TABLETOP.md",
            "ACCESS_REVIEW_TERMINATION_POLICY.md",
            "BUSINESS_ASSOCIATE_AGREEMENT_REVIEW.md",
            "CJIS_SECURITY_POLICY_MAPPING.md",
            "PERSONNEL_SECURITY_AWARENESS_POLICY.md",
            "ENCRYPTION_KEY_EVIDENCE.md",
            "VENDOR_SUBPROCESSOR_ASSESSMENT.md",
            "PRIVACY_LEGAL_LAUNCH_REVIEW.md",
            "USER_ACCEPTANCE_TEST_PLAN.md",
            "PHASE_VI_TEST_EVIDENCE.md",
            "COMPLIANCE_SOURCE_REGISTER.md",
            "PRODUCTION_ACCEPTANCE_EXERCISES.md",
            "STAGING_VALIDATION_RUNBOOK.md",
            "PHASE_VII_NATIONWIDE_SCALE.md",
            "REGIONAL_SUPPORT_DECISION_RECORD.md",
            "PHASE_VIII_DATA_LIFECYCLE_PRIVACY.md",
            "PRIVACY_REQUEST_RUNBOOK.md",
            "DATA_FLOW_INVENTORY.md",
            "PHASE_IX_RELEASE_AUTHORIZATION.md",
            "PILOT_TO_NATIONAL_ROLLOUT.md",
        )
        for document in required:
            self.assertTrue((REPOSITORY_ROOT / document).is_file(), document)

        phase_six = (
            REPOSITORY_ROOT / "PHASE_VI_COMPLIANCE_PRODUCT_READINESS.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Automated Chromium/WebKit browser and accessibility matrix", phase_six)
        self.assertIn("may not be represented as complete", phase_six)

    def test_staging_definition_keeps_production_boundaries_visible(self):
        compose = (REPOSITORY_ROOT / "compose.staging.yml").read_text(encoding="utf-8")
        runbook = (REPOSITORY_ROOT / "STAGING_VALIDATION_RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        client_dockerfile = (
            REPOSITORY_ROOT / "beaconsystems.client" / "Dockerfile"
        ).read_text(encoding="utf-8")

        for service in ("postgres:", "redis:", "clamav:", "migrate:", "api:", "worker:", "frontend:"):
            self.assertIn(service, compose)
        self.assertIn("service_completed_successfully", compose)
        self.assertIn("cannot satisfy production encryption evidence", runbook)
        self.assertIn("nginx-unprivileged", client_dockerfile)


if __name__ == "__main__":
    unittest.main()
