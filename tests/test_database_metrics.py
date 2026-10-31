from services.database_metrics import DatabaseMetrics


def test_database_metrics_use_bounded_non_sensitive_operation_labels():
    metrics = DatabaseMetrics()
    metrics.record(operation="select", duration_seconds=0.25, slow=False)
    metrics.record(operation="SELECT secret FROM evidence", duration_seconds=0.75, slow=True)

    output = metrics.render_prometheus()

    assert 'operation="SELECT"' in output
    assert 'operation="OTHER"' in output
    assert "secret" not in output
    assert 'beacon_database_slow_queries_total{operation="OTHER"} 1' in output
