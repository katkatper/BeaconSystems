import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ProductionConfigurationTests(unittest.TestCase):
    def test_main_has_no_wildcard_cors_or_unconditional_schema_bootstrap(self):
        source = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)

        self.assertNotIn('allow_origins=["*"]', source)
        self.assertEqual(source.count("Base.metadata.create_all(bind=engine)"), 1)
        self.assertIn("if ENABLE_LOCAL_SCHEMA_BOOTSTRAP:", source)
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
        self.assertIn("ENABLE_LOCAL_SCHEMA_BOOTSTRAP must be false", source)
        self.assertIn("SECRET_KEY must contain at least 32 characters", source)

    def test_database_pool_uses_health_checks_and_bounded_capacity(self):
        source = (REPOSITORY_ROOT / "database" / "connection.py").read_text(
            encoding="utf-8"
        )
        ast.parse(source)

        self.assertIn("pool_pre_ping=True", source)
        self.assertIn("pool_size=DATABASE_POOL_SIZE", source)
        self.assertIn("max_overflow=DATABASE_MAX_OVERFLOW", source)


if __name__ == "__main__":
    unittest.main()
