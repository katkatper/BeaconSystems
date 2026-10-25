import json
from pathlib import Path

from scripts.validate_assurance_evidence import validate

ROOT = Path(__file__).resolve().parents[1]


def test_assurance_template_is_valid_but_not_complete():
    record = json.loads(
        (ROOT / "config" / "assurance_evidence_template.json").read_text(encoding="utf-8")
    )
    assert validate(record) == []
    assert any("is not complete" in item for item in validate(record, require_complete=True))


def test_completed_assurance_record_passes_completeness_check():
    record = json.loads(
        (ROOT / "config" / "assurance_evidence_template.json").read_text(encoding="utf-8")
    )
    for section in ("exercises", "production_evidence", "approvals"):
        record[section] = {name: "passed" for name in record[section]}
    assert validate(record, require_complete=True) == []


def test_invalid_or_failed_status_is_rejected_for_release():
    record = json.loads(
        (ROOT / "config" / "assurance_evidence_template.json").read_text(encoding="utf-8")
    )
    record["approvals"]["security"] = "signed-by-someone"
    assert "invalid status" in " ".join(validate(record))
    record["approvals"]["security"] = "failed"
    assert any("security is not complete" in item for item in validate(record, True))
