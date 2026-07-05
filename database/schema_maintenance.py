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
            "evidence_latitude": "ALTER TABLE evidence ADD COLUMN evidence_latitude FLOAT",
            "evidence_longitude": "ALTER TABLE evidence ADD COLUMN evidence_longitude FLOAT",
            "geocode_provider": "ALTER TABLE evidence ADD COLUMN geocode_provider VARCHAR(50)",
            "geocode_accuracy": "ALTER TABLE evidence ADD COLUMN geocode_accuracy VARCHAR(50)",
            "geocode_score": "ALTER TABLE evidence ADD COLUMN geocode_score FLOAT",
            "geocoded_address": "ALTER TABLE evidence ADD COLUMN geocoded_address VARCHAR(500)",
            "geocoded_at": "ALTER TABLE evidence ADD COLUMN geocoded_at TIMESTAMP",
            "is_encrypted": "ALTER TABLE evidence ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE",
            "encryption_key_id": "ALTER TABLE evidence ADD COLUMN encryption_key_id VARCHAR(120)",
            "content_sha256": "ALTER TABLE evidence ADD COLUMN content_sha256 VARCHAR(64)",
        }

        for column_name, statement in evidence_columns.items():
            if not _has_column(inspector, "evidence", column_name):
                statements.append(statement)

    if "alerts" in table_names:
        alert_columns = {
            "alert_source": "ALTER TABLE alerts ADD COLUMN alert_source VARCHAR(100)",
            "source_detail": "ALTER TABLE alerts ADD COLUMN source_detail VARCHAR(255)",
            "confidence_score": "ALTER TABLE alerts ADD COLUMN confidence_score FLOAT",
        }

        for column_name, statement in alert_columns.items():
            if not _has_column(inspector, "alerts", column_name):
                statements.append(statement)

    if "bolo_alerts" in table_names:
        bolo_columns = {
            "latitude": "ALTER TABLE bolo_alerts ADD COLUMN latitude FLOAT",
            "longitude": "ALTER TABLE bolo_alerts ADD COLUMN longitude FLOAT",
            "geocode_provider": "ALTER TABLE bolo_alerts ADD COLUMN geocode_provider VARCHAR(50)",
            "geocode_accuracy": "ALTER TABLE bolo_alerts ADD COLUMN geocode_accuracy VARCHAR(50)",
            "geocode_score": "ALTER TABLE bolo_alerts ADD COLUMN geocode_score FLOAT",
            "geocoded_address": "ALTER TABLE bolo_alerts ADD COLUMN geocoded_address VARCHAR(500)",
            "geocoded_at": "ALTER TABLE bolo_alerts ADD COLUMN geocoded_at TIMESTAMP",
        }

        for column_name, statement in bolo_columns.items():
            if not _has_column(inspector, "bolo_alerts", column_name):
                statements.append(statement)

    if "sightings" in table_names:
        sighting_columns = {
            "geocode_provider": "ALTER TABLE sightings ADD COLUMN geocode_provider VARCHAR(50)",
            "geocode_accuracy": "ALTER TABLE sightings ADD COLUMN geocode_accuracy VARCHAR(50)",
            "geocode_score": "ALTER TABLE sightings ADD COLUMN geocode_score FLOAT",
            "geocoded_address": "ALTER TABLE sightings ADD COLUMN geocoded_address VARCHAR(500)",
            "geocoded_at": "ALTER TABLE sightings ADD COLUMN geocoded_at TIMESTAMP",
        }

        for column_name, statement in sighting_columns.items():
            if not _has_column(inspector, "sightings", column_name):
                statements.append(statement)

    geocode_columns = {
        "latitude": "FLOAT",
        "longitude": "FLOAT",
        "geocode_provider": "VARCHAR(50)",
        "geocode_accuracy": "VARCHAR(50)",
        "geocode_score": "FLOAT",
        "geocoded_address": "VARCHAR(500)",
        "geocoded_at": "TIMESTAMP",
    }

    for table_name in ["external_records", "partner_intake_records"]:
        if table_name in table_names:
            for column_name, column_type in geocode_columns.items():
                if not _has_column(inspector, table_name, column_name):
                    statements.append(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    )

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

    if "agency_exchanges" in table_names:
        agency_exchange_columns = {
            "requesting_officer": "ALTER TABLE agency_exchanges ADD COLUMN requesting_officer VARCHAR(200)",
            "badge_number": "ALTER TABLE agency_exchanges ADD COLUMN badge_number VARCHAR(80)",
            "subject": "ALTER TABLE agency_exchanges ADD COLUMN subject VARCHAR(255)",
            "request_type": "ALTER TABLE agency_exchanges ADD COLUMN request_type VARCHAR(120)",
            "priority": "ALTER TABLE agency_exchanges ADD COLUMN priority VARCHAR(50)",
            "due_date": "ALTER TABLE agency_exchanges ADD COLUMN due_date TIMESTAMP",
            "delivery_method": "ALTER TABLE agency_exchanges ADD COLUMN delivery_method VARCHAR(100)",
            "requested_records": "ALTER TABLE agency_exchanges ADD COLUMN requested_records TEXT",
            "attachments": "ALTER TABLE agency_exchanges ADD COLUMN attachments TEXT",
            "assigned_to": "ALTER TABLE agency_exchanges ADD COLUMN assigned_to VARCHAR(200)",
            "requested_by": "ALTER TABLE agency_exchanges ADD COLUMN requested_by INTEGER",
            "audit_log": "ALTER TABLE agency_exchanges ADD COLUMN audit_log TEXT",
            "submitted_at": "ALTER TABLE agency_exchanges ADD COLUMN submitted_at TIMESTAMP",
            "fulfilled_at": "ALTER TABLE agency_exchanges ADD COLUMN fulfilled_at TIMESTAMP",
        }

        for column_name, statement in agency_exchange_columns.items():
            if not _has_column(inspector, "agency_exchanges", column_name):
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
            "primary_address": "ALTER TABLE persons ADD COLUMN primary_address TEXT",
            "primary_address_latitude": "ALTER TABLE persons ADD COLUMN primary_address_latitude FLOAT",
            "primary_address_longitude": "ALTER TABLE persons ADD COLUMN primary_address_longitude FLOAT",
            "housing_status": "ALTER TABLE persons ADD COLUMN housing_status VARCHAR(50)",
            "school_name": "ALTER TABLE persons ADD COLUMN school_name VARCHAR(255)",
            "school_address": "ALTER TABLE persons ADD COLUMN school_address TEXT",
            "school_address_latitude": "ALTER TABLE persons ADD COLUMN school_address_latitude FLOAT",
            "school_address_longitude": "ALTER TABLE persons ADD COLUMN school_address_longitude FLOAT",
            "employer_name": "ALTER TABLE persons ADD COLUMN employer_name VARCHAR(255)",
            "work_address": "ALTER TABLE persons ADD COLUMN work_address TEXT",
            "work_address_latitude": "ALTER TABLE persons ADD COLUMN work_address_latitude FLOAT",
            "work_address_longitude": "ALTER TABLE persons ADD COLUMN work_address_longitude FLOAT",
            "employment_status": "ALTER TABLE persons ADD COLUMN employment_status VARCHAR(100)",
            "known_associates": "ALTER TABLE persons ADD COLUMN known_associates TEXT",
            "gang_affiliations": "ALTER TABLE persons ADD COLUMN gang_affiliations TEXT",
            "vehicles": "ALTER TABLE persons ADD COLUMN vehicles TEXT",
            "addresses": "ALTER TABLE persons ADD COLUMN addresses TEXT",
            "tips": "ALTER TABLE persons ADD COLUMN tips TEXT",
            "patterns": "ALTER TABLE persons ADD COLUMN patterns TEXT",
            "intelligence_notes": "ALTER TABLE persons ADD COLUMN intelligence_notes TEXT",
            "last_seen_latitude": "ALTER TABLE persons ADD COLUMN last_seen_latitude FLOAT",
            "last_seen_longitude": "ALTER TABLE persons ADD COLUMN last_seen_longitude FLOAT",
        }

        for column_name, statement in person_columns.items():
            if not _has_column(inspector, "persons", column_name):
                statements.append(statement)

    if "users" in table_names:
        user_columns = {
            "mfa_enabled": "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE",
            "mfa_secret": "ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(255)",
            "mfa_verified_at": "ALTER TABLE users ADD COLUMN mfa_verified_at TIMESTAMP",
            "last_login_at": "ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP",
        }

        for column_name, statement in user_columns.items():
            if not _has_column(inspector, "users", column_name):
                statements.append(statement)

    has_person_type_maintenance = "persons" in table_names

    if not statements and not has_person_type_maintenance:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

        if has_person_type_maintenance:
            connection.execute(text("ALTER TABLE persons ALTER COLUMN eye_color TYPE VARCHAR(100)"))
            connection.execute(text("ALTER TABLE persons ALTER COLUMN hair_color TYPE VARCHAR(150)"))
            connection.execute(text("ALTER TABLE persons ALTER COLUMN height TYPE VARCHAR(50)"))

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

        if "agency_exchanges" in table_names:
            connection.execute(
                text("UPDATE agency_exchanges SET priority = COALESCE(priority, 'routine')")
            )
            connection.execute(
                text("UPDATE agency_exchanges SET request_type = COALESCE(request_type, information_type)")
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
