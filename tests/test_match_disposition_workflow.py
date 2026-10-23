from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_match_review_is_tenant_scoped_reasoned_and_audited():
    source = (REPOSITORY_ROOT / "routes" / "match_routes.py").read_text(
        encoding="utf-8"
    )

    assert "Match.agency_id == current_user.agency_id" in source
    assert 'reason: str = Field(min_length=5, max_length=2000)' in source
    assert 'action="DISPOSITION_MATCH"' in source
    assert "A supervisor must reopen a final match decision" in source
    assert 'record.person_id = person.person_id' in source
    assert 'cursor_column=Match.id' in source
    assert "target_agency_id = agency_id" in source
    assert "run_agency_matching(" in source


def test_match_schema_records_reviewer_reason_and_time():
    model = (REPOSITORY_ROOT / "models" / "match.py").read_text(encoding="utf-8")
    migration = (
        REPOSITORY_ROOT
        / "migrations"
        / "versions"
        / "1b4e88d3c295_add_match_disposition_workflow.py"
    ).read_text(encoding="utf-8")

    for field in ("disposition_reason", "reviewed_by_user_id", "reviewed_at", "updated_at"):
        assert field in model
        assert field in migration
    assert 'down_revision = "0a3d77c2b184"' in migration
    assert "ix_matches_agency_status_created" in migration


def test_intelligence_center_requires_human_match_disposition():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "IntelligenceCenter.jsx"
    ).read_text(encoding="utf-8")

    assert 'fetch(apiUrl("/matches/?limit=100")' in source
    assert "Beacon provides a score, not a final identity decision" in source
    assert "Confirm Match" in source
    assert "Need More Information" in source
    assert "Reject Match" in source
