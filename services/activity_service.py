from models.activity_log import ActivityLog


#ACTIVITY LOG TO DATABASE

def create_activity_log(

    db,

    action: str,

    entity: str,

    user_id: int | None = None,

    agency_id: int | None = None,

    entity_id: int | None = None,

    details: str | None = None,

    ip_address: str | None = None,
):


    log = ActivityLog(

        user_id=user_id,

        agency_id=agency_id,

        action=action,

        entity=entity,

        entity_id=entity_id,

        details=details,

        ip_address=ip_address,
    )

    db.add(log)
    db.commit()
    db.refresh(log)


    return log