"""Validate Beacon's production configuration inventory without exposing secrets."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

PLACEHOLDER_MARKERS = ("change-me", "change_me", "replace-with", "example-secret")


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required_keys = {"schema_version", "required", "alternatives", "secret", "tracked"}
    if set(manifest) != required_keys or manifest["schema_version"] != 1:
        raise RuntimeError("Production environment manifest schema is invalid")
    lists = [manifest[name] for name in ("required", "secret", "tracked")]
    if not all(isinstance(items, list) for items in lists):
        raise RuntimeError("Production environment manifest lists are invalid")
    if any(len(items) != len(set(items)) for items in lists):
        raise RuntimeError("Production environment manifest contains duplicate names")
    return manifest


def validate_environment(manifest: dict, environment: dict[str, str]) -> dict:
    missing = sorted(name for name in manifest["required"] if not environment.get(name))
    for alternative in manifest["alternatives"]:
        if not any(
            all(environment.get(name) for name in option)
            for option in alternative["options"]
        ):
            missing.append(alternative["name"])

    placeholders = sorted(
        name
        for name in manifest["secret"]
        if environment.get(name)
        and any(marker in environment[name].lower() for marker in PLACEHOLDER_MARKERS)
    )
    public_snapshot = {
        name: environment.get(name, "") for name in sorted(manifest["tracked"])
    }
    fingerprint = hashlib.sha256(
        json.dumps(public_snapshot, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "status": "valid" if not missing and not placeholders else "invalid",
        "schema_version": manifest["schema_version"],
        "configuration_fingerprint": fingerprint,
        "missing": missing,
        "placeholder_secrets": placeholders,
        "secret_presence": {
            name: bool(environment.get(name)) for name in sorted(manifest["secret"])
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-manifest", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "config" / "production_environment_manifest.json")
    if args.check_manifest:
        result = {"status": "valid", "schema_version": manifest["schema_version"]}
    else:
        result = validate_environment(manifest, dict(os.environ))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        reason = str(exc) if isinstance(exc, RuntimeError) else "validation failed"
        print(json.dumps({"status": "failed", "reason": reason}), file=sys.stderr)
        sys.exit(1)
