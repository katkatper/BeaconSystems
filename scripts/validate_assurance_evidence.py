"""Validate a redacted Beacon assurance record without treating a template as approval."""

import argparse
import json
from pathlib import Path

ALLOWED = {"pending", "passed", "failed", "not_applicable"}
SECTIONS = ("exercises", "production_evidence", "approvals")


def validate(record: dict, require_complete: bool = False) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    for field in ("release_id", "commit", "environment", "evidence_date_utc", "owners"):
        if field not in record:
            errors.append(f"missing field: {field}")
    for section in SECTIONS:
        values = record.get(section)
        if not isinstance(values, dict) or not values:
            errors.append(f"{section} must be a non-empty object")
            continue
        for name, status in values.items():
            if status not in ALLOWED:
                errors.append(f"{section}.{name} has invalid status: {status}")
            if require_complete and status not in {"passed", "not_applicable"}:
                errors.append(f"{section}.{name} is not complete")
    if not isinstance(record.get("evidence_links", []), list):
        errors.append("evidence_links must be an array")
    if not isinstance(record.get("open_risks", []), list):
        errors.append("open_risks must be an array")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("config/assurance_evidence_template.json"),
    )
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    record = json.loads(args.path.read_text(encoding="utf-8"))
    errors = validate(record, require_complete=args.require_complete)
    print(json.dumps({"status": "invalid" if errors else "valid", "errors": errors}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
