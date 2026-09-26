import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DeploymentPackagingTests(unittest.TestCase):
    def test_production_dependencies_are_exactly_pinned(self):
        requirements = (
            REPOSITORY_ROOT / "requirements.txt"
        ).read_text(encoding="utf-8").splitlines()
        dependencies = [line for line in requirements if line and not line.startswith("#")]
        self.assertTrue(dependencies)
        self.assertTrue(all("==" in line for line in dependencies))

    def test_container_runs_as_non_root_and_has_a_healthcheck(self):
        source = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("USER 10001:10001", source)
        self.assertIn("HEALTHCHECK", source)
        self.assertIn('CMD ["python", "scripts/start_production.py"]', source)
        self.assertNotIn("COPY . .", source)

    def test_container_context_excludes_private_and_generated_content(self):
        source = (REPOSITORY_ROOT / ".dockerignore").read_text(encoding="utf-8")
        for entry in [".git", ".env", "docs", "uploads", "node_modules", "tests"]:
            self.assertIn(entry, source)

    def test_production_launcher_uses_environment_runtime_controls(self):
        source = (
            REPOSITORY_ROOT / "scripts" / "start_production.py"
        ).read_text(encoding="utf-8")
        for setting in ["API_BIND_HOST", "API_PORT", "API_WORKERS", "FORWARDED_ALLOW_IPS"]:
            self.assertIn(setting, source)
        self.assertIn("proxy_headers=True", source)


if __name__ == "__main__":
    unittest.main()
