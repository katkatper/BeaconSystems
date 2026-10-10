import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    REPOSITORY_ROOT
    / "migrations"
    / "versions"
    / "a7d31c9e4b20_add_dashboard_query_indexes.py"
)


def test_dashboard_index_migration_extends_current_head_and_is_reversible():
    source = MIGRATION_PATH.read_text(encoding="utf-8")
    ast.parse(source)

    assert 'down_revision = "f6c28db137ba"' in source
    assert "op.create_index" in source
    assert "op.drop_index" in source


def test_dashboard_indexes_cover_observed_filter_and_sort_paths():
    source = MIGRATION_PATH.read_text(encoding="utf-8")

    expected_indexes = {
        "ix_alerts_case_created",
        "ix_sightings_case_created",
        "ix_agency_exchanges_case_created",
        "ix_legal_access_agency_status",
        "ix_case_access_grants_agency_granted",
    }
    for index_name in expected_indexes:
        assert index_name in source

    # Leads are used by the application but are not yet represented in the
    # Alembic-managed schema. Do not reference a table that clean deployments
    # cannot create.
    assert "ix_leads_case_status" not in source


def test_dashboard_indexes_are_declared_in_model_metadata():
    expected_model_indexes = {
        "alerts.py": "ix_alerts_case_created",
        "sighting.py": "ix_sightings_case_created",
        "agency_exchange.py": "ix_agency_exchanges_case_created",
        "legal_access_request.py": "ix_legal_access_agency_status",
        "case_access_grant.py": "ix_case_access_grants_agency_granted",
        "leads.py": "ix_leads_case_status",
    }

    for file_name, index_name in expected_model_indexes.items():
        source = (REPOSITORY_ROOT / "models" / file_name).read_text(encoding="utf-8")
        assert index_name in source, file_name
