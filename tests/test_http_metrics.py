from services.http_metrics import HttpMetrics


def test_http_metrics_use_bounded_route_and_status_labels():
    metrics = HttpMetrics()
    metrics.record(
        method="GET",
        route="/cases/{case_id}",
        status_code=200,
        duration=0.125,
    )
    metrics.record(
        method="TRACE-ATTACK",
        route="raw-user-input",
        status_code=599,
        duration=-1,
    )

    output = metrics.render_prometheus(
        {"database": True, "evidence_storage": False}
    )

    assert 'route="/cases/{case_id}"' in output
    assert 'status_class="2xx"' in output
    assert 'method="OTHER",route="unmatched",status_class="5xx"' in output
    assert 'component="database"} 1' in output
    assert 'component="evidence_storage"} 0' in output
    assert "0.125000" in output


def test_system_metrics_endpoint_requires_privileged_role_contract():
    from pathlib import Path

    source = Path("routes/jobs_routes.py").read_text(encoding="utf-8")
    assert '@router.get("/metrics/system/prometheus"' in source
    assert 'require_role("platform_admin", "agency_admin", "supervisor")' in source
    assert "readiness_service.snapshot()" in source
