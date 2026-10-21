from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_lead_workflow_is_case_scoped_same_agency_and_audited():
    source = (REPOSITORY_ROOT / "routes" / "leads_routes.py").read_text(
        encoding="utf-8"
    )

    assert "apply_related_case_access_filter" in source
    assert "assert_case_write_access" in source
    assert "assignee.agency_id != case.agency_id" in source
    assert "Investigators may only assign leads to themselves" in source
    assert 'action="CREATE_LEAD"' in source
    assert 'action="UPDATE_LEAD"' in source
    assert "A resolution is required to close a lead" in source


def test_lead_schema_tracks_owner_priority_due_date_and_closure():
    model = (REPOSITORY_ROOT / "models" / "leads.py").read_text(encoding="utf-8")
    migration = (
        REPOSITORY_ROOT
        / "migrations"
        / "versions"
        / "0a3d77c2b184_add_lead_ownership_workflow.py"
    ).read_text(encoding="utf-8")

    for field in ("assigned_to_user_id", "priority", "due_at", "resolution", "closed_at"):
        assert field in model
        assert field in migration
    assert 'down_revision = "f29c66b19573"' in migration
    assert "fk_leads_case" in migration
    assert "ix_leads_assignee_status" in migration


def test_case_profile_uses_real_lead_records_instead_of_placeholder_counts():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "CaseDetail.jsx"
    ).read_text(encoding="utf-8")

    assert 'fetch(apiUrl(`/leads/?case_id=${id}`)' in source
    assert 'fetch(apiUrl(`/leads/assignees?case_id=${id}`)' in source
    assert "submitLead" in source
    assert "updateLead" in source
    assert "New leads: {externalRecords.length}" not in source
