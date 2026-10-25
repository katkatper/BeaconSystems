"""Validate Beacon's versioned nationwide capacity planning contract."""

import json
from pathlib import Path

PLAN = Path("config/nationwide_capacity_plan.json")


def validate(plan: dict) -> list[str]:
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if plan.get("status") not in {"provisional", "approved"}:
        errors.append("status must be provisional or approved")
    for section in ("targets", "service_levels"):
        values = plan.get(section)
        if not isinstance(values, dict) or not values:
            errors.append(f"{section} must be a non-empty object")
            continue
        for name, value in values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                errors.append(f"{section}.{name} must be greater than zero")
    if not plan.get("required_results"):
        errors.append("required_results must not be empty")
    return errors


def main() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    errors = validate(plan)
    print(json.dumps({"status": "invalid" if errors else "valid", "errors": errors}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
