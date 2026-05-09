from Models.sightings import sightings

from services.alert_service import trigger_alert

def create_sighting(db, data):

    sighting= sightings(**data.dict())

    db.add(sighting)
    db.commit()
    db.refresh(sighting)

    trigger_alert(sighting)

    return sighting


