from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_intelligence_map_uses_supported_three_timer():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "IntelligenceMap3D.jsx"
    ).read_text(encoding="utf-8")

    assert "new Clock(" not in source
    assert "new Timer()" in source
    assert "timer.update(timestamp)" in source
    assert "timer.dispose()" in source


def test_dashboard_polling_is_visibility_aware_and_non_overlapping():
    dashboard_source = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "pages" / "Dashboard.jsx"
    ).read_text(encoding="utf-8")
    polling_source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "hooks"
        / "useVisiblePolling.js"
    ).read_text(encoding="utf-8")

    assert "useVisiblePolling" in dashboard_source
    assert "10000" not in dashboard_source
    assert "document.hidden" in polling_source
    assert "inFlight" in polling_source
    assert 'removeEventListener("visibilitychange"' in polling_source
