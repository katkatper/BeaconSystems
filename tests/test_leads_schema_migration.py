import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_leads_model_uses_normalized_table_name():
    model_source = (REPOSITORY_ROOT / "models" / "leads.py").read_text(
        encoding="utf-8"
    )
    assert '__tablename__ = "leads"' in model_source


def test_leads_migration_handles_legacy_and_clean_databases():
    migration_source = (
        REPOSITORY_ROOT
        / "migrations"
        / "versions"
        / "b8e42da7c531_reconcile_leads_table.py"
    ).read_text(encoding="utf-8")
    ast.parse(migration_source)

    assert 'down_revision = "a7d31c9e4b20"' in migration_source
    assert 'op.rename_table("Leads", "leads")' in migration_source
    assert 'op.create_table(' in migration_source
    assert '"ix_leads_case_status"' in migration_source
    assert 'op.rename_table("leads", "Leads")' in migration_source
