from sqlalchemy import event, text
from sqlalchemy.orm import Session


TENANT_AGENCY_KEY = "beacon.agency_id"
PLATFORM_ADMIN_KEY = "beacon.platform_admin"


def _postgresql_tenant_settings(connection, agency_id, platform_admin) -> None:
    if connection.dialect.name != "postgresql":
        return

    connection.execute(
        text("SELECT set_config(:key, :value, true)"),
        {"key": TENANT_AGENCY_KEY, "value": str(agency_id or "")},
    )
    connection.execute(
        text("SELECT set_config(:key, :value, true)"),
        {
            "key": PLATFORM_ADMIN_KEY,
            "value": "true" if platform_admin else "false",
        },
    )


@event.listens_for(Session, "after_begin")
def restore_tenant_context(session, transaction, connection) -> None:
    if "tenant_platform_admin" not in session.info:
        return

    _postgresql_tenant_settings(
        connection,
        session.info.get("tenant_agency_id"),
        session.info["tenant_platform_admin"],
    )


def configure_tenant_session(
    session: Session,
    *,
    agency_id: int | None,
    platform_admin: bool,
) -> None:
    if agency_id is None and not platform_admin:
        raise RuntimeError("A tenant-scoped session requires an agency")

    session.info["tenant_agency_id"] = agency_id
    session.info["tenant_platform_admin"] = platform_admin

    # Authentication may already have opened the transaction before the tenant
    # was known, so apply the settings immediately as well as on future begins.
    connection = session.connection()
    _postgresql_tenant_settings(connection, agency_id, platform_admin)
