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


def test_application_shell_supports_keyboard_and_screen_reader_navigation():
    app_source = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "App.jsx"
    ).read_text(encoding="utf-8")
    styles = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "App.css"
    ).read_text(encoding="utf-8")

    assert 'className="skip-link"' in app_source
    assert 'href="#main-content"' in app_source
    assert 'id="main-content"' in app_source
    assert 'tabIndex="-1"' in app_source
    assert "main.focus({ preventScroll: true })" in app_source
    assert ":focus-visible" in styles
    assert "prefers-reduced-motion: reduce" in styles
    assert "forced-colors: active" in styles


def test_mobile_acceptance_contract_preserves_touch_targets_and_content():
    styles = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "App.css"
    ).read_text(encoding="utf-8")
    checklist = (
        REPOSITORY_ROOT
        / "PHASE_III_MOBILE_ACCESSIBILITY_ACCEPTANCE.md"
    ).read_text(encoding="utf-8")

    assert "min-height: 44px" in styles
    assert "font-size: 16px" in styles
    assert ".beacon-page table" in styles
    assert "320 CSS pixels" in checklist
    assert "200% browser zoom" in checklist
    assert "NVDA" in checklist
    assert "VoiceOver" in checklist
    assert "TalkBack" in checklist


def test_case_tabs_support_keyboard_and_screen_reader_navigation():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "CaseDetail.jsx"
    ).read_text(encoding="utf-8")

    assert 'role="tablist"' in source
    assert 'role="tab"' in source
    assert "aria-selected={activeTab === tabId}" in source
    assert 'role="tabpanel"' in source
    assert 'event.key === "ArrowRight"' in source
    assert 'event.key === "ArrowLeft"' in source
    assert 'event.key === "Home"' in source
    assert 'event.key === "End"' in source


def test_investigator_workspace_has_refresh_and_live_notification_feedback():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "InvestigatorWorkspace.jsx"
    ).read_text(encoding="utf-8")

    assert "Refresh workspace" in source
    assert 'aria-live="polite"' in source
    assert "Notification marked read." in source
    assert "Workspace access unavailable" in source
    assert "Try again" in source
    assert "markingNotificationId" in source
    styles = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "App.css"
    ).read_text(encoding="utf-8")
    assert ".sr-only" in styles
    assert ".workspace-error-state" in styles


def test_api_errors_preserve_http_status_for_permission_states():
    source = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "api.jsx"
    ).read_text(encoding="utf-8")
    assert "error.status = response.status" in source


def test_access_tokens_are_tab_scoped_instead_of_persisted_locally():
    client_root = REPOSITORY_ROOT / "beaconsystems.client" / "src"
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in client_root.rglob("*")
        if path.suffix in {".js", ".jsx"}
    )

    assert 'localStorage.getItem("token")' not in sources
    assert 'localStorage.setItem("token"' not in sources
    assert 'localStorage.removeItem("token")' not in sources
    helper = (client_root / "authSession.js").read_text(encoding="utf-8")
    assert '"token"' in helper
    assert "sessionStorage.getItem(key)" in helper
    assert "sessionStorage.setItem(key" in helper
    assert "sessionStorage.removeItem(key)" in helper


def test_authentication_metadata_is_tab_scoped_and_centralized():
    client_root = REPOSITORY_ROOT / "beaconsystems.client" / "src"
    helper = (client_root / "authSession.js").read_text(encoding="utf-8")
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in client_root.rglob("*")
        if path.suffix in {".js", ".jsx"}
    )

    for key in ("token", "role", "username", "agency_id", "session_expires_at"):
        assert f'localStorage.setItem("{key}"' not in sources
    assert "AUTH_SESSION_KEYS" in helper
    assert "storeAuthSession" in helper
    assert "clearAuthSession" in helper


def test_protected_routes_verify_identity_with_the_server_before_rendering():
    app = (REPOSITORY_ROOT / "beaconsystems.client" / "src" / "App.jsx").read_text(encoding="utf-8")

    assert 'apiGet("/users/me")' in app
    assert "updateSessionIdentity(identity)" in app
    assert 'identityStatus !== "verified"' in app
    assert "Verifying secure session" in app


def test_beacon_insight_starts_collapsed_without_covering_operational_controls():
    source = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "components"
        / "BeaconInsight.jsx"
    ).read_text(encoding="utf-8")
    assert "const [collapsed, setCollapsed] = useState(true)" in source
    assert 'window.matchMedia("(max-width: 700px)").matches' not in source


def test_frontend_restricted_routes_have_role_guards_and_safe_denial_state():
    source = (
        REPOSITORY_ROOT / "beaconsystems.client" / "src" / "App.jsx"
    ).read_text(encoding="utf-8")
    assert "function RoleRoute" in source
    assert 'role="alert"' in source
    assert "No restricted data was loaded." in source
    assert 'const administratorRoles = ["platform_admin", "agency_admin"]' in source
    assert source.count("<RoleRoute allowedRoles=") >= 20
