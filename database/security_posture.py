from sqlalchemy import text


RLS_TABLES = (
    "cases",
    "alerts",
    "bolo_alerts",
    "case_access_grants",
    "case_team_members",
    "external_records",
    "legal_access_requests",
    "matches",
    "partner_intake_records",
)


def database_role_violations(
    *,
    is_superuser: bool,
    bypasses_rls: bool,
    owned_tables: list[str],
    unprotected_tables: list[str],
) -> list[str]:
    violations = []
    if is_superuser:
        violations.append("application database role must not be a superuser")
    if bypasses_rls:
        violations.append("application database role must not have BYPASSRLS")
    if owned_tables:
        violations.append(
            "application database role must not own protected tables: "
            + ", ".join(sorted(owned_tables))
        )
    if unprotected_tables:
        violations.append(
            "required Row Level Security is missing: "
            + ", ".join(sorted(unprotected_tables))
        )
    return violations


def validate_database_security(engine) -> None:
    if engine.dialect.name != "postgresql":
        raise RuntimeError("Production database must be PostgreSQL")

    with engine.connect() as connection:
        role = connection.execute(
            text(
                """
                SELECT rolsuper, rolbypassrls
                FROM pg_roles
                WHERE rolname = current_user
                """
            )
        ).one()

        table_status = connection.execute(
            text(
                """
                SELECT
                    tables.table_name,
                    roles.rolname = current_user AS owned_by_application,
                    classes.relrowsecurity,
                    EXISTS (
                        SELECT 1
                        FROM pg_policies
                        WHERE schemaname = 'public'
                          AND tablename = tables.table_name
                          AND policyname = 'beacon_tenant_isolation'
                    ) AS has_tenant_policy
                FROM unnest(CAST(:table_names AS text[])) AS tables(table_name)
                LEFT JOIN pg_class AS classes
                    ON classes.relname = tables.table_name
                    AND classes.relnamespace = 'public'::regnamespace
                LEFT JOIN pg_roles AS roles ON roles.oid = classes.relowner
                """
            ),
            {"table_names": list(RLS_TABLES)},
        ).all()

    owned_tables = [
        row.table_name for row in table_status if row.owned_by_application
    ]
    unprotected_tables = [
        row.table_name
        for row in table_status
        if not row.relrowsecurity or not row.has_tenant_policy
    ]
    violations = database_role_violations(
        is_superuser=role.rolsuper,
        bypasses_rls=role.rolbypassrls,
        owned_tables=owned_tables,
        unprotected_tables=unprotected_tables,
    )
    if violations:
        raise RuntimeError(
            "Unsafe production database configuration: "
            + "; ".join(violations)
        )
