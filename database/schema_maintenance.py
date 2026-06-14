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
            "is_encrypted": "ALTER TABLE evidence ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE",
            "encryption_key_id": "ALTER TABLE evidence ADD COLUMN encryption_key_id VARCHAR(120)",
            "content_sha256": "ALTER TABLE evidence ADD COLUMN content_sha256 VARCHAR(64)",
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

    if "legal_access_requests" in table_names:
        legal_request_columns = {
            "person_id": "ALTER TABLE legal_access_requests ADD COLUMN person_id INTEGER",
            "assigned_investigator_id": "ALTER TABLE legal_access_requests ADD COLUMN assigned_investigator_id INTEGER",
            "approved_by_user_id": "ALTER TABLE legal_access_requests ADD COLUMN approved_by_user_id INTEGER",
            "request_type": "ALTER TABLE legal_access_requests ADD COLUMN request_type VARCHAR(100)",
            "receiving_entity": "ALTER TABLE legal_access_requests ADD COLUMN receiving_entity VARCHAR(255)",
            "reason_for_request": "ALTER TABLE legal_access_requests ADD COLUMN reason_for_request TEXT",
            "probable_cause_summary": "ALTER TABLE legal_access_requests ADD COLUMN probable_cause_summary TEXT",
            "attachments": "ALTER TABLE legal_access_requests ADD COLUMN attachments TEXT",
            "priority": "ALTER TABLE legal_access_requests ADD COLUMN priority VARCHAR(50)",
            "due_date": "ALTER TABLE legal_access_requests ADD COLUMN due_date TIMESTAMP",
        }

        for column_name, statement in legal_request_columns.items():
            if not _has_column(inspector, "legal_access_requests", column_name):
                statements.append(statement)

    if "persons" in table_names:
        person_columns = {
            "criminal_arrests_count": "ALTER TABLE persons ADD COLUMN criminal_arrests_count INTEGER",
            "felony_convictions_count": "ALTER TABLE persons ADD COLUMN felony_convictions_count INTEGER",
            "active_warrants_count": "ALTER TABLE persons ADD COLUMN active_warrants_count INTEGER",
            "protective_orders_count": "ALTER TABLE persons ADD COLUMN protective_orders_count INTEGER",
            "last_arrest_date": "ALTER TABLE persons ADD COLUMN last_arrest_date TIMESTAMP",
            "most_serious_offense": "ALTER TABLE persons ADD COLUMN most_serious_offense VARCHAR(255)",
            "criminal_history": "ALTER TABLE persons ADD COLUMN criminal_history TEXT",
            "warrants": "ALTER TABLE persons ADD COLUMN warrants TEXT",
            "arrests": "ALTER TABLE persons ADD COLUMN arrests TEXT",
            "charges": "ALTER TABLE persons ADD COLUMN charges TEXT",
            "convictions": "ALTER TABLE persons ADD COLUMN convictions TEXT",
            "corrections_history": "ALTER TABLE persons ADD COLUMN corrections_history TEXT",
            "known_associates": "ALTER TABLE persons ADD COLUMN known_associates TEXT",
            "gang_affiliations": "ALTER TABLE persons ADD COLUMN gang_affiliations TEXT",
            "vehicles": "ALTER TABLE persons ADD COLUMN vehicles TEXT",
            "addresses": "ALTER TABLE persons ADD COLUMN addresses TEXT",
            "tips": "ALTER TABLE persons ADD COLUMN tips TEXT",
            "patterns": "ALTER TABLE persons ADD COLUMN patterns TEXT",
            "intelligence_notes": "ALTER TABLE persons ADD COLUMN intelligence_notes TEXT",
        }

        for column_name, statement in person_columns.items():
            if not _has_column(inspector, "persons", column_name):
                statements.append(statement)

    if "users" in table_names:
        user_columns = {
            "mfa_enabled": "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE",
            "mfa_verified_at": "ALTER TABLE users ADD COLUMN mfa_verified_at TIMESTAMP",
            "last_login_at": "ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP",
        }

        for column_name, statement in user_columns.items():
            if not _has_column(inspector, "users", column_name):
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
            connection.execute(
                text("UPDATE evidence SET is_encrypted = COALESCE(is_encrypted, FALSE)")
            )

        if "users" in table_names:
            connection.execute(
                text("UPDATE users SET mfa_enabled = COALESCE(mfa_enabled, FALSE)")
            )

        if "legal_access_requests" in table_names:
            connection.execute(
                text("UPDATE legal_access_requests SET priority = COALESCE(priority, 'routine')")
            )
            connection.execute(
                text("UPDATE legal_access_requests SET request_type = COALESCE(request_type, authority_type)")
            )
            connection.execute(
                text("UPDATE legal_access_requests SET receiving_entity = COALESCE(receiving_entity, requester_organization)")
            )
            connection.execute(
                text("UPDATE legal_access_requests SET reason_for_request = COALESCE(reason_for_request, purpose)")
            )
            connection.execute(
                text("UPDATE legal_access_requests SET probable_cause_summary = COALESCE(probable_cause_summary, scope_description)")
            )

        if "persons" in table_names:
            connection.execute(
                text("UPDATE persons SET criminal_arrests_count = COALESCE(criminal_arrests_count, 0)")
            )
            connection.execute(
                text("UPDATE persons SET felony_convictions_count = COALESCE(felony_convictions_count, 0)")
            )
            connection.execute(
                text("UPDATE persons SET active_warrants_count = COALESCE(active_warrants_count, 0)")
            )
            connection.execute(
                text("UPDATE persons SET protective_orders_count = COALESCE(protective_orders_count, 0)")
            )
