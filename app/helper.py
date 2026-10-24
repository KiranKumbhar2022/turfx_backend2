
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.owner.models import turf_model as models
from app.client.models.user_turf_model import Booking
from app.owner.schemas import turf_schema


def build_booking_response(db: Session, booking: Booking):
    turf = db.scalar(
        select(models.Turf)
        .where(models.Turf.id == booking.turf_id)
        .options(
            selectinload(models.Turf.equipment),
            selectinload(models.Turf.schedule),
            selectinload(models.Turf.media),
        )
    )

    if turf is None:
        raise HTTPException(status_code=404, detail="Turf not found")

    # Calculate booking duration in hours
    start = datetime.strptime(str(booking.start_time), "%H:%M:%S")
    end = datetime.strptime(str(booking.end_time), "%H:%M:%S")

    duration_hours = (end - start).total_seconds() / 3600

    # Calculate turf amount
    turf_amount = float(turf.price_per_hour or 0) * duration_hours

    # Calculate selected equipment amount
    selected_equipment = booking.selected_equipment or []

    equipment_amount = sum(
        float(item.get("subtotal") or (
            float(item.get("price") or 0)
            * int(item.get("quantity") or 1)
        ))
        for item in selected_equipment
    )

    # Final payable amount
    payable_amount = round(turf_amount + equipment_amount, 2)

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "turf_id": booking.turf_id,
        "sport": booking.sport,
        "booking_date": booking.booking_date,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "total_amount": booking.total_amount,
        "payable_amount": payable_amount,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "created_at": booking.created_at,
        "selected_equipment": selected_equipment,
        "turf": turf_schema.TurfOut.model_validate(turf),
    }
