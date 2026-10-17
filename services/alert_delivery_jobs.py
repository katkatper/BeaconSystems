from sqlalchemy.orm import Session

from models.alert_delivery import AlertDelivery
from services.clock import utc_now
from services.job_handlers import register_job_handler


@register_job_handler("alert.deliver")
def handle_alert_delivery(db: Session, job) -> None:
    delivery_id = int(job.payload["delivery_id"])
    delivery = db.query(AlertDelivery).filter(
        AlertDelivery.delivery_id == delivery_id,
        AlertDelivery.agency_id == job.agency_id,
    ).first()
    if not delivery:
        raise ValueError("Alert delivery does not exist for the job tenant")
    if delivery.status in {"delivered", "viewed", "acknowledged"}:
        return

    now = utc_now()
    delivery.status = "delivered"
    delivery.sent_at = delivery.sent_at or now
    delivery.delivered_at = delivery.delivered_at or now
    delivery.updated_at = now
    db.flush()
