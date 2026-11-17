
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.owner.models import turf_model as models
from app.client.models.user_turf_model import Booking
from app.owner.schemas import turf_schema
from sqlalchemy import select, update, or_, and_
from zoneinfo import ZoneInfo
from app.owner.models import turf_model

import smtplib

from email.message import EmailMessage

from app.core.config import setting

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
        raise HTTPException(
            status_code=404,
            detail="Turf not found"
        )

    selected_equipment = booking.selected_equipment or []

    # Get saved booking amounts
    turf_amount = float(booking.turf_amount or 0)
    equipment_amount = float(booking.equipment_amount or 0)
    total_amount = float(booking.total_amount or 0)

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "turf_id": booking.turf_id,
        "sport": booking.sport,
        "booking_date": booking.booking_date,
        "start_time": booking.start_time,
        "end_time": booking.end_time,

        # Booking amounts
        "turf_amount": turf_amount,
        "equipment_amount": equipment_amount,
        "total_amount": total_amount,
        "payable_amount": total_amount,

        "status": booking.status,
        "payment_status": booking.payment_status,
        "created_at": booking.created_at,

        "selected_equipment": selected_equipment,

        "turf": turf_schema.TurfOut.model_validate(turf),
    }


def update_completed_bookings(db, owner_id):

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    owner_turf_ids = select(
        turf_model.Turf.id
    ).where(
        turf_model.Turf.owner_id == owner_id
    )

    result = db.execute(
        update(Booking)
        .where(
            Booking.turf_id.in_(owner_turf_ids),
            Booking.status == "confirmed",
            or_(
                Booking.booking_date < now.date(),
                and_(
                    Booking.booking_date == now.date(),
                    Booking.end_time <= now.time().replace(
                        tzinfo=None
                    )
                )
            )
        )
        .values(status="completed")
    )

    db.commit()

    print(
        f"Completed bookings updated: {result.rowcount}"
    )


def send_owner_reset_email(
    email: str,
    reset_token: str
):
    reset_link = (
        f"{setting.FRONTEND_URL}/reset-password"
        f"?token={reset_token}"
    )

    message = EmailMessage()

    message["Subject"] = "TurfX - Password Reset"
    message["From"] = setting.SMTP_EMAIL
    message["To"] = email

    message.set_content(
        f"""
Hello,

We received a request to reset your TurfX owner account password.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request this password reset,
please ignore this email.

Regards,
TurfX Team
"""
    )

    with smtplib.SMTP(
        setting.SMTP_HOST,
        setting.SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            setting.SMTP_EMAIL,
            setting.SMTP_PASSWORD
        )

        server.send_message(message)
