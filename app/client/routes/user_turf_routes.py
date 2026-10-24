from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
import httpx

from app.database.database import getDB
from app.owner.models import turf_model 
from app.owner.schemas import turf_schema
from app.client.dependencies.dependencies import get_current_user
import logging

from datetime import datetime, time
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from app.helper import build_booking_response
from app.client.models.user_turf_model import Booking
from datetime import date, datetime, time, timedelta

from app.client.models.user_turf_model import Booking

from app.client.schemas.user_turf_schema import (
    CheckoutRequest,
    BookingOut,
    BookingListResponse,
    BookingDetailsResponse,
)
from app.client.schemas.user_turf_schema   import (
    CityLocationResponse,
    CitySearchResponse,
)

logger = logging.getLogger(__name__)

routes = APIRouter(
    prefix="/user",
    tags=["User Turfs"],
)


@routes.get(
    "/turfs",
    response_model=turf_schema.TurfListResponse
)
def get_turfs_by_location(
    city: str = Query(..., min_length=1),
    state: str | None = None,
    country: str | None = None,
    play_type: turf_schema.PlayType | None = None,
    max_price: float | None = Query(default=None, gt=0),
    search: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(getDB),
):


    stmt = select(turf_model.Turf)
    stmt = stmt.where(
        func.lower(turf_model.Turf.city) == city.strip().lower()
    )
    if state:
        stmt = stmt.where(
            func.lower(turf_model.Turf.state) == state.strip().lower()
        )
    if country:
        stmt = stmt.where(
            func.lower(turf_model.Turf.country) == country.strip().lower()
        )
    if play_type:
        stmt = stmt.where(
            turf_model.Turf.play_types.contains(play_type.value)
        )

    if max_price is not None:
        stmt = stmt.where(
            turf_model.Turf.price_per_hour <= max_price
        )

    if search:
        stmt = stmt.where(
            turf_model.Turf.name.ilike(f"%{search.strip()}%")
        )

    stmt = stmt.order_by(turf_model.Turf.id.desc())
    stmt = stmt.offset(skip).limit(limit)

    turfs = db.scalars(stmt).all()

    return turf_schema.TurfListResponse(
        status_code=200,
        message="Turfs fetched successfully",
        response=turfs
    )


@routes.get(
    "/turfs/{turf_id}",
    response_model=turf_schema.TurfDetailsResponse
)
def get_turf_by_id(
    turf_id: int,
    db: Session = Depends(getDB),
):
    stmt = (
        select(turf_model.Turf)
        .where(turf_model.Turf.id == turf_id)
        .options(
            selectinload(turf_model.Turf.equipment),
            selectinload(turf_model.Turf.schedule),
            selectinload(turf_model.Turf.media),
        )
    )

    turf = db.scalars(stmt).first()

    if turf is None:
        raise HTTPException(
            status_code=404,
            detail="Turf not found"
        )

    return turf_schema.TurfDetailsResponse(
        status_code=200,
        message="Turf fetched successfully",
        response=turf
    )


@routes.post(
    "/turfs/{turf_id}/favorite",
    response_model=turf_schema.FavoriteTurfResponse,
)
def check_turf_favorite(
    turf_id: int,
    db: Session = Depends(getDB),
    current_user=Depends(get_current_user),
):
    turf = db.get(turf_model.Turf, turf_id)

    if turf is None:
        raise HTTPException(
            status_code=404,
            detail="Turf not found",
        )

    favorite = db.scalar(
        select(turf_model.FavoriteTurf).where(
            turf_model.FavoriteTurf.user_id == current_user.id,
            turf_model.FavoriteTurf.turf_id == turf_id,
        )
    )

    return turf_schema.FavoriteTurfResponse(
        status_code=200,
        message="Favorite status fetched successfully",
        turf_id=turf_id,
        is_favorite=favorite is not None,
    )

@routes.get("/favorites", response_model=turf_schema.TurfListResponse)
def get_favorite_turfs(
    db: Session = Depends(getDB),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(turf_model.Turf)
        .join(
            turf_model.FavoriteTurf,
            turf_model.FavoriteTurf.turf_id == turf_model.Turf.id,
        )
        .where(turf_model.FavoriteTurf.user_id == current_user.id)
        .options(
            selectinload(turf_model.Turf.equipment),
            selectinload(turf_model.Turf.schedule),
            selectinload(turf_model.Turf.media),
        )
        .order_by(turf_model.FavoriteTurf.id.desc())
    )

    turfs = db.scalars(stmt).all()

    favorite_turfs = [
        turf_schema.TurfOut.model_validate(turf).model_copy(
            update={"isFavorite": True}
        )
        for turf in turfs
    ]

    return turf_schema.TurfListResponse(
        status_code=200,
        message="Favorite turfs fetched successfully",
        response=favorite_turfs,
    )

@routes.post(
    "/checkout",
    response_model=BookingDetailsResponse,
    status_code=201,
)
def checkout_booking(
    payload: CheckoutRequest,
    db: Session = Depends(getDB),
    current_user=Depends(get_current_user),
):
    # 1. Validate booking time
    if payload.start_time >= payload.end_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be later than start time",
        )

    booking_start = datetime.combine(
        payload.booking_date,
        payload.start_time,
    )

    if booking_start <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Please select a future booking time",
        )

    # 2. Fetch turf and related information
    turf = db.scalar(
        select(turf_model.Turf)
        .where(turf_model.Turf.id == payload.turf_id)
        .options(
            selectinload(turf_model.Turf.equipment),
            selectinload(turf_model.Turf.schedule),
            selectinload(turf_model.Turf.media),
        )
    )

    if turf is None:
        raise HTTPException(
            status_code=404,
            detail="Turf not found",
        )

    # 3. Validate selected sport
    available_sports = turf.play_types or ""

    if isinstance(available_sports, str):
        available_sports = [
            sport.strip().lower()
            for sport in available_sports.split(",")
        ]
    else:
        available_sports = [
            str(sport).strip().lower()
            for sport in available_sports
        ]

    if payload.sport.strip().lower() not in available_sports:
        raise HTTPException(
            status_code=400,
            detail="Selected sport is not available at this turf",
        )

    # 4. Check whether the selected slot is already booked
    conflict = db.scalar(
        select(Booking.id)
        .where(
            Booking.turf_id == payload.turf_id,
            Booking.booking_date == payload.booking_date,
            Booking.status.in_(["pending", "confirmed"]),
            Booking.start_time < payload.end_time,
            Booking.end_time > payload.start_time,
        )
        .limit(1)
    )

    if conflict is not None:
        raise HTTPException(
            status_code=409,
            detail="This time slot is already booked",
        )

    # 5. Calculate turf booking price
    duration_seconds = (
        datetime.combine(payload.booking_date, payload.end_time)
        - datetime.combine(payload.booking_date, payload.start_time)
    ).total_seconds()

    duration_hours = duration_seconds / 3600

    total_amount = float(turf.price_per_hour) * duration_hours

    # 6. Validate selected equipment and calculate equipment charges
    turf_equipment = {
        item.id: item for item in (turf.equipment or [])
    }

    selected_equipment = []
    seen_ids = set()

    for requested in (payload.equipment or []):
        if requested.equipment_id in seen_ids:
            raise HTTPException(
                status_code=400,
                detail="Duplicate equipment IDs are not allowed",
            )

        seen_ids.add(requested.equipment_id)

        item = turf_equipment.get(requested.equipment_id)

        if item is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Equipment {requested.equipment_id} "
                    "is not available at this turf"
                ),
            )

        price = float(item.price or 0)
        subtotal = price * requested.quantity

        total_amount += subtotal

        selected_equipment.append(
            {
                "equipment_id": item.id,
                "item": item.item,
                "price": price,
                "quantity": requested.quantity,
                "subtotal": round(subtotal, 2),
            }
        )

    # 7. Prepare booking record
    booking = Booking(
        user_id=current_user.id,
        turf_id=turf.id,
        sport=payload.sport.strip(),
        booking_date=payload.booking_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        total_amount=round(total_amount, 2),
        status="pending",
        payment_status="unpaid",
        selected_equipment=selected_equipment,
    )

    # 8. Save booking to the database
    try:
        db.add(booking)
        db.commit()
        db.refresh(booking)

    except Exception as e:
        db.rollback()

        # Print full traceback in the FastAPI terminal
        logger.exception("Failed to create booking")

        # Temporary debugging response; avoid exposing raw errors in production
        raise HTTPException(
            status_code=500,
            detail=f"Unable to create booking: {str(e)}",
        ) from e

    # 9. Return successful response
    return BookingDetailsResponse(
        status_code=201,
        message="Booking created successfully",
        response=build_booking_response(db, booking),
    )

@routes.get(
    "/bookings/pending",
    response_model=BookingListResponse,
)
def get_pending_bookings(
    db: Session = Depends(getDB),
    current_user=Depends(get_current_user),
):
    bookings = db.scalars(
        select(Booking)
        .where(
            Booking.user_id == current_user.id,
            Booking.status == "pending",
        )
        .order_by(Booking.created_at.desc())
    ).all()

    booking_responses = [
        build_booking_response(db, booking)
        for booking in bookings
    ]

    return BookingListResponse(
        status_code=200,
        message="Pending bookings fetched successfully",
        response=booking_responses,
    )

@routes.get(
    "/bookings/{booking_id}",
    response_model=BookingDetailsResponse,
)
def get_booking_details(
    booking_id: int,
    db: Session = Depends(getDB),
    current_user=Depends(get_current_user),
):
    booking = db.scalar(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == current_user.id,
        )
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    return BookingDetailsResponse(
        status_code=200,
        message="Booking fetched successfully",
        response=booking,
    )


@routes.get(
    "/turfs/{turf_id}/available-slots",
    response_model=turf_schema.AvailableSlotsResponse,
)
def get_available_time_slots(
    turf_id: int,
    booking_date: date = Query(...),
    slot_duration: int = Query(default=60, ge=15, le=240),
    db: Session = Depends(getDB),
):
    # 1. Validate the booking date
    today = date.today()

    if booking_date < today:
        raise HTTPException(
            status_code=400,
            detail="Booking date cannot be in the past",
        )

    # 2. Fetch turf and its schedule
    stmt = (
        select(turf_model.Turf)
        .where(turf_model.Turf.id == turf_id)
        .options(
            selectinload(turf_model.Turf.schedule),
        )
    )

    turf = db.scalars(stmt).first()

    if turf is None:
        raise HTTPException(
            status_code=404,
            detail="Turf not found",
        )

    # 3. Find the schedule for the selected weekday
    # Monday = 0, Tuesday = 1, ..., Sunday = 6
    weekday = booking_date.weekday()

    schedule = next(
        (
            item
            for item in turf.schedule
            if item.day == weekday and item.is_open
        ),
        None,
    )

    if schedule is None:
        return turf_schema.AvailableSlotsResponse(
            status_code=200,
            message="Turf is closed on the selected date",
            turf_id=turf_id,
            booking_date=booking_date,
            slot_duration=slot_duration,
            available_slots=[],
        )

    opening_time = schedule.open_time
    closing_time = schedule.close_time

    if opening_time >= closing_time:
        raise HTTPException(
            status_code=400,
            detail="Invalid turf opening schedule",
        )

    # 4. Fetch existing bookings for this turf and date
    booked_rows = db.execute(
        select(
            Booking.start_time,
            Booking.end_time,
        ).where(
            Booking.turf_id == turf_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(["pending", "confirmed"]),
        )
    ).all()

    # 5. Generate time slots
    available_slots = []

    current_start = datetime.combine(
        booking_date,
        opening_time,
    )

    closing_datetime = datetime.combine(
        booking_date,
        closing_time,
    )

    # Local server time is used for today's past-slot check.
    now = datetime.now()
    slot_length = timedelta(minutes=slot_duration)

    while current_start + slot_length <= closing_datetime:
        current_end = current_start + slot_length

        # Skip slots that have already started or are in the past
        if booking_date == today and current_start <= now:
            current_start += slot_length
            continue

        # 6. Check whether this slot overlaps an existing booking
        is_booked = any(
            booked_start < current_end.time()
            and booked_end > current_start.time()
            for booked_start, booked_end in booked_rows
        )

        # Include both booked and available slots
        available_slots.append(
        turf_schema.AvailableTimeSlot(
        start_time=current_start.time(),
        end_time=current_end.time(),
        is_booked=is_booked,
    )
)

        current_start += slot_length

    # 7. Return response
    return turf_schema.AvailableSlotsResponse(
    status_code=200,
    message="Available time slots fetched successfully",
    turf_id=turf_id,
    booking_date=booking_date,
    slot_duration=slot_duration,
    available_slots=available_slots,
)




@routes.get(
    "/locations/search",
    response_model=CitySearchResponse,
)
def search_city(
    city: str = Query(..., min_length=2, max_length=100),
):
    city = city.strip()

    if len(city) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid city name",
        )

    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": city,
                "countrycodes": "in",
                "featureType": "city",
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 1,
            },
            headers={
                "User-Agent": "TurfX/1.0 (city location search)",
            },
            timeout=10.0,
        )

        response.raise_for_status()
        results = response.json()

    except (httpx.HTTPError, ValueError) as exc:
        print(f"City search error: {exc}")

        raise HTTPException(
            status_code=502,
            detail="Unable to search city right now. Please try again.",
        )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="City not found",
        )

    city_data = results[0]
    address = city_data.get("address", {})

    city_info = CityLocationResponse(
        name=(
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or city_data.get("name")
            or city
        ),
        state=address.get("state"),
        country=address.get("country"),
        latitude=float(city_data["lat"]),
        longitude=float(city_data["lon"]),
    )

    return CitySearchResponse(
        status_code=200,
        message="City fetched successfully",
        city=city_info,
    )
