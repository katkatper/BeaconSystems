import ast
from pathlib import Path

from services.capacity_usage import UsageMetric

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_usage_metric_reports_remaining_percent_and_limit_state():
    metric = UsageMetric(used=75, quota=100).as_dict()

    assert metric == {
        "used": 75,
        "quota": 100,
        "remaining": 25,
        "percent_used": 75.0,
        "exceeded": False,
    }
    assert UsageMetric(used=100, quota=100).as_dict()["exceeded"] is True
    assert UsageMetric(used=7, quota=None).as_dict()["remaining"] is None


def test_capacity_endpoint_is_role_and_tenant_bounded():
    source = (REPOSITORY_ROOT / "routes" / "capacity_routes.py").read_text(
        encoding="utf-8"
    )
    ast.parse(source)

    assert 'require_role("platform_admin", "agency_admin", "supervisor")' in source
    assert 'current_user.role != "platform_admin"' in source
    assert "current_user.agency_id != agency_id" in source


def test_storage_quota_is_checked_before_object_storage_write():
    source = (REPOSITORY_ROOT / "routes" / "evidence_routes.py").read_text(
        encoding="utf-8"
    )
    quota_check = source.index("agency_storage_bytes(db, agency_id) + upload_size")
    storage_write = source.index("object_storage.put(file.file")

    assert quota_check < storage_write
    assert 'status_code=413, detail="Agency storage quota exceeded"' in source
    assert "file_size_bytes=stored.size_bytes" in source


def test_capacity_migration_adds_positive_quotas_and_usage_index():
    source = (
        REPOSITORY_ROOT
        / "migrations"
        / "versions"
        / "5a7d36c9e104_add_agency_capacity_quotas.py"
    ).read_text(encoding="utf-8")
    ast.parse(source)

    assert "storage_quota_bytes" in source
    assert "monthly_provider_request_quota" in source
    assert "monthly_job_quota" in source
    assert "file_size_bytes" in source
    assert "ix_partner_intake_agency_received" in source
