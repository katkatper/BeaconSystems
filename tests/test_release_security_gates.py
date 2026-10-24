from pathlib import Path


def test_release_workflow_generates_sboms_and_scans_both_images():
    workflow = Path(".github/workflows/release-gates.yml").read_text(encoding="utf-8")

    assert "anchore/sbom-action@v0.24.0" in workflow
    assert "beacon-api-sbom.cdx.json" in workflow
    assert "beacon-worker-sbom.cdx.json" in workflow
    assert "aquasecurity/trivy-action@v0.36.0" in workflow
    assert workflow.count("severity: HIGH,CRITICAL") == 2
    assert workflow.count("exit-code: 1") == 2
    assert "retention-days: 30" in workflow
