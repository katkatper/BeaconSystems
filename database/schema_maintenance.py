from sqlalchemy import inspect, text


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def ensure_local_schema(engine) -> None:
    """Patch known local-dev schema drift that create_all cannot repair."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    statements = []

    if "evidence" in table_names:
        evidence_columns = {
            "custody_status": "ALTER TABLE evidence ADD COLUMN custody_status VARCHAR(100)",
            "current_holder": "ALTER TABLE evidence ADD COLUMN current_holder VARCHAR(200)",
            "lab_reference": "ALTER TABLE evidence ADD COLUMN lab_reference VARCHAR(200)",
            "available_at": "ALTER TABLE evidence ADD COLUMN available_at TIMESTAMP",
        }

        for column_name, statement in evidence_columns.items():
            if not _has_column(inspector, "evidence", column_name):
                statements.append(statement)

    if "evidence_chain" in table_names:
        chain_columns = {
            "from_holder": "ALTER TABLE evidence_chain ADD COLUMN from_holder VARCHAR(200)",
            "to_holder": "ALTER TABLE evidence_chain ADD COLUMN to_holder VARCHAR(200)",
            "location": "ALTER TABLE evidence_chain ADD COLUMN location VARCHAR(200)",
            "available_at": "ALTER TABLE evidence_chain ADD COLUMN available_at TIMESTAMP",
        }

        for column_name, statement in chain_columns.items():
            if not _has_column(inspector, "evidence_chain", column_name):
                statements.append(statement)

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

        if "evidence" in table_names:
            connection.execute(
                text("UPDATE evidence SET custody_status = COALESCE(custody_status, 'collected')")
            )
