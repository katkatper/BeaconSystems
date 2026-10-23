from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_notification_api_is_scoped_to_authenticated_user_and_tenant():
    source = (REPOSITORY_ROOT / "routes" / "notifications_routes.py").read_text(
        encoding="utf-8"
    )

    assert "Notification.agency_id == current_user.agency_id" in source
    assert "Notification.user_id == current_user.user_id" in source
    assert 'action="READ_NOTIFICATION"' in source
    assert 'action="READ_ALL_NOTIFICATIONS"' in source
    assert "paginate_query(" in source
    assert "cursor_column=Notification.notification_id" in source


def test_alert_creation_notifies_only_the_assigned_active_investigator():
    service = (REPOSITORY_ROOT / "services" / "notification_service.py").read_text(
        encoding="utf-8"
    )
    alert_route = (REPOSITORY_ROOT / "routes" / "alerts_routes.py").read_text(
        encoding="utf-8"
    )
    alert_service = (REPOSITORY_ROOT / "services" / "alert_service.py").read_text(
        encoding="utf-8"
    )

    assert "User.user_id == case.investigator_id" in service
    assert "User.agency_id == case.agency_id" in service
    assert 'User.role == "investigator"' in service
    assert "User.is_active.is_(True)" in service
    assert "notify_assigned_investigator_of_alert(" in alert_route
    assert "notify_assigned_investigator_of_alert(" in alert_service


def test_notification_schema_and_ui_use_durable_read_receipts():
    model = (REPOSITORY_ROOT / "models" / "notification.py").read_text(
        encoding="utf-8"
    )
    migration = (
        REPOSITORY_ROOT
        / "migrations"
        / "versions"
        / "2c5f91a8d730_add_investigator_notifications.py"
    ).read_text(encoding="utf-8")
    workspace = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "InvestigatorWorkspace.jsx"
    ).read_text(encoding="utf-8")
    command_tools = (
        REPOSITORY_ROOT
        / "beaconsystems.client"
        / "src"
        / "pages"
        / "CommandTools.jsx"
    ).read_text(encoding="utf-8")

    assert "read_at" in model
    assert 'down_revision = "1b4e88d3c295"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "/notifications/${notificationId}/read" in workspace
    assert 'apiGet("/notifications/?limit=100")' in command_tools
    assert 'apiPost("/notifications/read-all"' in command_tools
