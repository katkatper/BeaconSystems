import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_leads_model_uses_normalized_table_name():
    model_source = (REPOSITORY_ROOT / "models" / "leads.py").read_text(
        encoding="utf-8"
    )
    assert '__tablename__ = "leads"' in model_source


def test_baseline_creates_normalized_leads_schema():
    migration_source = (
        REPOSITORY_ROOT
        / "migrations"
        / "versions"
        / "601d95116833_create_beacon_production_baseline.py"
    ).read_text(encoding="utf-8")
    ast.parse(migration_source)

    assert "op.create_table('leads'" in migration_source
    assert "'ix_leads_case_status'" in migration_source
    assert "op.drop_table('leads')" in migration_source
