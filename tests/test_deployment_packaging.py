import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _load_hygiene_module():
    module_path = REPOSITORY_ROOT / "scripts" / "check_repository_hygiene.py"
    spec = spec_from_file_location("check_repository_hygiene", module_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def test_repository_hygiene_rejects_dependency_artifact_variants(self):
        hygiene = _load_hygiene_module()
        for path in [
            "beaconsystems.client/.bin/npm.cmd",
            "beaconsystems.client/node_modules_old/native.node",
            ".venv-py314-backup/Lib/package.py",
        ]:
            with self.subTest(path=path):
                self.assertTrue(hygiene.forbidden_tracked(path))

    def test_production_launcher_uses_environment_runtime_controls(self):
        source = (
            REPOSITORY_ROOT / "scripts" / "start_production.py"
        ).read_text(encoding="utf-8")
        for setting in ["API_BIND_HOST", "API_PORT", "API_WORKERS", "FORWARDED_ALLOW_IPS"]:
            self.assertIn(setting, source)
        self.assertIn("proxy_headers=True", source)

    def test_release_gates_include_security_scans(self):
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release-gates.yml"
        ).read_text(encoding="utf-8")
        development_requirements = (
            REPOSITORY_ROOT / "requirements-dev.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("python -m pip_audit", workflow)
        self.assertIn("python -m bandit", workflow)
        self.assertIn("python -m ruff check", workflow)
        self.assertIn("--cov-fail-under=23", workflow)
        self.assertIn("npm audit --omit=dev --audit-level=moderate", workflow)
        self.assertIn("bandit==", development_requirements)
        self.assertIn("pip-audit==", development_requirements)
        self.assertIn("ruff==", development_requirements)


if __name__ == "__main__":
    unittest.main()
