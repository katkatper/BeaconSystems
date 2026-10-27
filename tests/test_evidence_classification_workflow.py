from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_upload_requires_supported_classification_and_retention():
    source = (REPOSITORY_ROOT / "routes" / "evidence_routes.py").read_text(
        encoding="utf-8"
    )

    assert 'normalized_type not in EVIDENCE_TYPES' in source
    assert 'normalized_retention not in UPLOAD_RETENTION_POLICIES' in source
    assert 'detail="Collection time cannot be in the future"' in source
    assert "is_sensitive=is_sensitive" in source
    assert "retention_policy_code=normalized_retention" in source
    assert "collected_at=collected_at or utc_now()" in source


def test_investigator_upload_uses_authorized_case_and_structured_fields():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "EvidenceUpload.jsx"
    ).read_text(encoding="utf-8")

    assert 'apiGet("/cases/?limit=100")' in source
    assert "Select an authorized case" in source
    assert 'formData.append("is_sensitive"' in source
    assert 'formData.append("retention_policy_code"' in source
    assert 'formData.append("collected_at"' in source
    assert "Scan & Upload Evidence" in source
