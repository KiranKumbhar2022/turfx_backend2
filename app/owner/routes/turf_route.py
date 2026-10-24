from fastapi import APIRouter, Depends, HTTPException, Query, logger, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.owner.schemas import turf_schema  
from app.owner.models import turf_model as models
from app.database.database import getDB
from app.helper import build_booking_response
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.client.models.user_turf_model import Booking
from app.owner.models import turf_model
from app.owner.dependencies.dependecies import getCurrentOwner

from app.owner.schemas.turf_schema import (
    BookingDecisionRequest,
    OwnerBookingRequestsResponse,
    BookingDecisionResponse,
)

routes = APIRouter(prefix="/turf-owner/turfs", tags=["Turfs"])


def _set_schedule(turf: models.Turf, days: list[turf_schema.ScheduleDayIn]):
    turf.schedule = [
        models.ScheduleDay(
            day=d.day.value,
            is_open=d.is_open,
            open_time=d.open_time,
            close_time=d.close_time,
        )
        for d in sorted(days, key=lambda x: x.day.value)
    ]


def _set_equipment(turf: models.Turf, items: list[turf_schema.EquipmentIn]):
    turf.equipment = [models.Equipment(item=e.item, price=e.price) for e in items]


def _get_or_404(db: Session, turf_id: int) -> models.Turf:
    turf = db.get(models.Turf, turf_id)
    if not turf:
        raise HTTPException(status_code=404, detail="Turf not found")
    return turf

@routes.post(
    "/create",
    response_model=turf_schema.TurfOut,
    status_code=status.HTTP_201_CREATED,
)
def create_turf(
    payload: turf_schema.TurfCreate,
    db: Session = Depends(getDB),
    current_user=Depends(getCurrentOwner),
):
    """Creates a turf with equipment and weekly schedule."""

    turf = models.Turf(
    owner_id=current_user.id,
    name=payload.name,
    description=payload.description,
    price_per_hour=payload.price_per_hour,
    play_types=",".join(p.value for p in payload.play_types),
    rental_enabled=payload.rental_enabled,
    city=payload.city,
    state=payload.state,
    country=payload.country,
    latitude=payload.latitude,
    longitude=payload.longitude,
)

    _set_equipment(turf, payload.equipment)
    _set_schedule(turf, payload.schedule)

    db.add(turf)
    db.commit()
    db.refresh(turf)

    return turf

@routes.get("", response_model=list[turf_schema.TurfOut])
def list_turfs(
    play_type: turf_schema.PlayType | None = None,
    max_price: float | None = Query(default=None, gt=0),
    search: str | None = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(getDB),
):
    stmt = select(models.Turf)
    if play_type:
        stmt = stmt.where(models.Turf.play_types.contains(play_type.value))
    if max_price:
        stmt = stmt.where(models.Turf.price_per_hour <= max_price)
    if search:
        stmt = stmt.where(models.Turf.name.ilike(f"%{search}%"))
    return db.scalars(stmt.offset(skip).limit(limit)).all()


@routes.get("/{turf_id}", response_model=turf_schema.TurfOut)
def get_turf(turf_id: int, db: Session = Depends(getDB)):
    return _get_or_404(db, turf_id)


@routes.patch("/{turf_id}", response_model=turf_schema.TurfOut)
def update_turf(
    turf_id: int, payload: turf_schema.TurfUpdate, db: Session = Depends(getDB)
):
    turf = _get_or_404(db, turf_id)

    for field in ("name", "description", "price_per_hour", "rental_enabled"):
        value = getattr(payload, field)
        if value is not None:
            setattr(turf, field, value)
    if payload.play_types is not None:
        turf.play_types = ",".join(p.value for p in payload.play_types)
    if payload.equipment is not None:
        _set_equipment(turf, payload.equipment)
    if payload.schedule is not None:
        _set_schedule(turf, payload.schedule)
    if not turf.rental_enabled:
        turf.equipment = []

    db.commit()
    db.refresh(turf)
    return turf


@routes.delete("/{turf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turf(turf_id: int, db: Session = Depends(getDB)):
    db.delete(_get_or_404(db, turf_id))
    db.commit()


# --------------------------------------------------
# 1. Get pending booking requests for owner's turfs
# --------------------------------------------------
@routes.get(
    "/bookings/requests",
    response_model=OwnerBookingRequestsResponse,
)
def get_owner_booking_requests(
    db: Session = Depends(getDB),
    current_user=Depends(getCurrentOwner),
):
    bookings = db.scalars(
        select(Booking)
        .join(
            turf_model.Turf,
            Booking.turf_id == turf_model.Turf.id,
        )
        .where(
            turf_model.Turf.owner_id == current_user.id,
            Booking.status == "pending",
        )
        .options(
            selectinload(Booking.turf)
        )
        .order_by(Booking.id.desc())
    ).all()

    return OwnerBookingRequestsResponse(
        status_code=200,
        message="Pending booking requests fetched successfully",
        response=[
            build_booking_response(db, booking)
            for booking in bookings
        ],
    )

# --------------------------------------------------
# 2. Accept or reject a booking request
# --------------------------------------------------
@routes.patch(
    "/turf-owner/bookings/{booking_id}/decision",
    response_model=BookingDecisionResponse,
)
def decide_booking_request(
    booking_id: int,
    payload: BookingDecisionRequest,
    db: Session = Depends(getDB),
    current_user=Depends(getCurrentOwner),
):
    # Find booking only if it belongs to the owner's turf.
    booking = db.scalar(
        select(Booking)
        .join(
            turf_model.Turf,
            Booking.turf_id == turf_model.Turf.id,
        )
        .where(
            Booking.id == booking_id,
            turf_model.Turf.owner_id == current_user.id,
        )
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking request not found",
        )

    # Only pending requests can be decided.
    if booking.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                f"This booking has already been "
                f"{booking.status}"
            ),
        )

    if payload.action == "accept":
        booking.status = "confirmed"
        message = "Booking request accepted successfully"

    else:
        booking.status = "rejected"
        message = "Booking request rejected successfully"

    try:
        db.commit()
        db.refresh(booking)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to update booking decision: %s",
            booking_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to update booking request",
        )

    return BookingDecisionResponse(
        status_code=200,
        message=message,
        response=build_booking_response(db, booking),
    )
