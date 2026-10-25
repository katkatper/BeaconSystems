import json
from pathlib import Path

from scripts.validate_capacity_plan import validate

ROOT = Path(__file__).resolve().parents[1]


def test_nationwide_capacity_plan_is_versioned_and_provisional():
    plan = json.loads(
        (ROOT / "config" / "nationwide_capacity_plan.json").read_text(encoding="utf-8")
    )
    assert validate(plan) == []
    assert plan["status"] == "provisional"
    assert "multi_tenant_isolation_under_load" in plan["required_results"]


def test_capacity_validator_rejects_missing_or_nonpositive_targets():
    plan = {"schema_version": 1, "status": "approved", "targets": {"rps": 0},
            "service_levels": {"p95": 1}, "required_results": ["load"]}
    assert "targets.rps must be greater than zero" in validate(plan)


def test_final_phase_documents_keep_external_authority_visible():
    required = (
        "PHASE_VII_NATIONWIDE_SCALE.md",
        "REGIONAL_SUPPORT_DECISION_RECORD.md",
        "PHASE_VIII_DATA_LIFECYCLE_PRIVACY.md",
        "PRIVACY_REQUEST_RUNBOOK.md",
        "DATA_FLOW_INVENTORY.md",
        "PHASE_IX_RELEASE_AUTHORIZATION.md",
        "PILOT_TO_NATIONAL_ROLLOUT.md",
    )
    for name in required:
        assert (ROOT / name).is_file(), name
    authorization = (ROOT / "PHASE_IX_RELEASE_AUTHORIZATION.md").read_text(encoding="utf-8")
    assert "necessary but insufficient" in authorization
    assert "No approval may be inferred" in authorization
