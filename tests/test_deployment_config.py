import json
from pathlib import Path

from scripts.validate_deployment_config import load_manifest, validate_environment

MANIFEST_PATH = Path("config/production_environment_manifest.json")


def complete_environment(manifest):
    environment = {name: "configured" for name in manifest["required"]}
    environment["DATABASE_URL"] = "postgresql://user:private@db/beacon"
    for name in manifest["tracked"]:
        environment.setdefault(name, "configured")
    return environment


def test_manifest_is_versioned_and_accepts_complete_configuration():
    manifest = load_manifest(MANIFEST_PATH)
    result = validate_environment(manifest, complete_environment(manifest))
    assert result["status"] == "valid"
    assert len(result["configuration_fingerprint"]) == 64


def test_validator_reports_missing_and_placeholders_without_secret_values():
    manifest = load_manifest(MANIFEST_PATH)
    environment = complete_environment(manifest)
    environment["SECRET_KEY"] = "replace-with-super-secret-value"
    environment.pop("CORS_ORIGINS")

    result = validate_environment(manifest, environment)
    serialized = json.dumps(result)

    assert result["status"] == "invalid"
    assert "CORS_ORIGINS" in result["missing"]
    assert "SECRET_KEY" in result["placeholder_secrets"]
    assert "replace-with-super-secret-value" not in serialized
    assert "private" not in serialized
