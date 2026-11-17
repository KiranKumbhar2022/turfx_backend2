
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.database import getDB
from app.client.models.user_turf_model import Booking
from app.owner.models import turf_model
from app.helper import build_booking_response
from app.helper import update_completed_bookings
from app.owner.schemas.turf_schema import OwnerBookingDetailResponse

# Use your existing owner authentication dependency
from app.owner.dependencies.dependecies import getCurrentOwner
from app.client.models.auth_model import clientAuthModel

from app.owner.schemas.turf_schema import OwnerBookingRequestsResponse
from app.owner.models import turf_model as models

routes = APIRouter(
    prefix="/turf-owner/bookings",
    tags=["Owner Bookings"],
)


@routes.get(
    "",
    response_model=OwnerBookingRequestsResponse,
)
def get_owner_bookings(
    status: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(getDB),
    current_owner=Depends(getCurrentOwner),
):

    # 1. Fetch owner's bookings
    stmt = (
        select(Booking)
        .join(
            turf_model.Turf,
            Booking.turf_id == turf_model.Turf.id,
        )
        .where(
            turf_model.Turf.owner_id == current_owner.id
        )
        .options(
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.equipment
            ),
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.schedule
            ),
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.media
            ),
        )
    )

    # 2. Filter by booking status
    if status:
        stmt = stmt.where(
            Booking.status == status.strip().lower()
        )

    # 3. Latest bookings first
    stmt = stmt.order_by(
        Booking.created_at.desc(),
        Booking.id.desc(),
    )

    # 4. Pagination
    stmt = stmt.offset(skip).limit(limit)

    bookings = db.scalars(stmt).unique().all()

    # 5. Get all customer IDs
    user_ids = list({
        booking.user_id for booking in bookings
    })

    # 6. Fetch customer details in one query
    customers = db.scalars(
        select(clientAuthModel).where(
            clientAuthModel.id.in_(user_ids)
        )
    ).all() if user_ids else []

    customer_map = {
        customer.id: customer
        for customer in customers
    }

    # 7. Build booking response with customer details
    booking_responses = []

    for booking in bookings:

        booking_data = build_booking_response(
            db, booking
        )

        customer = customer_map.get(booking.user_id)

        booking_data["customer"] = (
            {
                "id": customer.id,
                "name": customer.name,
                "mobile": customer.phone,
                "email": customer.email,
                "profile_image": customer.profile_image,
            }
            if customer else None
        )

        booking_responses.append(booking_data)

    return OwnerBookingRequestsResponse(
        status_code=200,
        message="Owner bookings fetched successfully",
        response=booking_responses,
    )


@routes.get(
    "/history",
    response_model=OwnerBookingRequestsResponse,
)
def get_owner_booking_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(getDB),
    current_owner=Depends(getCurrentOwner),
):

    update_completed_bookings(
        db,
        current_owner.id
    )
    # 1. Fetch only completed bookings of logged-in owner
    stmt = (
        select(Booking)
        .join(
            turf_model.Turf,
            Booking.turf_id == turf_model.Turf.id,
        )
        .where(
            turf_model.Turf.owner_id == current_owner.id,
            Booking.status == "completed",
        )
        .options(
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.equipment
            ),
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.schedule
            ),
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.media
            ),
        )
    )

    # 2. Latest completed bookings first
    stmt = stmt.order_by(
        Booking.booking_date.desc(),
        Booking.end_time.desc(),
        Booking.id.desc(),
    )

    # 3. Pagination
    stmt = stmt.offset(skip).limit(limit)

    bookings = db.scalars(stmt).unique().all()

    # 4. Get customer IDs
    user_ids = list({
        booking.user_id for booking in bookings
    })

    # 5. Fetch customer details
    customers = db.scalars(
        select(clientAuthModel).where(
            clientAuthModel.id.in_(user_ids)
        )
    ).all() if user_ids else []

    customer_map = {
        customer.id: customer
        for customer in customers
    }

    # 6. Build booking response
    booking_responses = []

    for booking in bookings:

        booking_data = build_booking_response(
            db, booking
        )

        customer = customer_map.get(booking.user_id)

        booking_data["customer"] = (
            {
                "id": customer.id,
                "name": customer.name,
                "mobile": customer.phone,
                "email": customer.email,
                "profile_image": customer.profile_image,
            }
            if customer else None
        )

        booking_responses.append(booking_data)

    return OwnerBookingRequestsResponse(
        status_code=200,
        message="Owner booking history fetched successfully",
        response=booking_responses,
    )



@routes.get(
    "/{booking_id}",
    response_model=OwnerBookingDetailResponse,
)
def get_owner_booking_details(
    booking_id: int,
    db: Session = Depends(getDB),
    current_owner=Depends(getCurrentOwner),
):

    # 1. Fetch booking with turf details
    stmt = (
        select(Booking)
        .join(
            turf_model.Turf,
            Booking.turf_id == turf_model.Turf.id,
        )
        .where(
            Booking.id == booking_id,
            turf_model.Turf.owner_id == current_owner.id,
        )
        .options(
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.equipment
            ),
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.schedule
            ),
            selectinload(Booking.turf).selectinload(
                turf_model.Turf.media
            ),
        )
    )

    booking = db.scalars(stmt).unique().first()

    # 2. Check booking exists
    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    # 3. Fetch customer details
    customer = db.scalars(
        select(clientAuthModel).where(
            clientAuthModel.id == booking.user_id
        )
    ).first()

    # 4. Build booking response
    booking_data = build_booking_response(
        db, booking
    )

    # 5. Add customer details
    booking_data["customer"] = (
        {
            "id": customer.id,
            "name": customer.name,
            "mobile": customer.phone,
            "email": customer.email,
            "profile_image": customer.profile_image,
        }
        if customer else None
    )

    # 6. Return response
    return OwnerBookingDetailResponse(
        status_code=200,
        message="Booking details fetched successfully",
        response=booking_data,
    )


# ACCEPT BOOKING
@routes.patch("/{booking_id}/accept")
def accept_booking(
    booking_id: int,
    db: Session = Depends(getDB),
    current_owner=Depends(getCurrentOwner)
):
    # Find booking
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Verify turf belongs to logged-in owner
    turf = db.query(models.Turf).filter(
        models.Turf.id == booking.turf_id,
        models.Turf.owner_id == current_owner.id
    ).first()

    if not turf:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage this booking"
        )

    # Only pending bookings can be accepted
    if booking.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Booking is already {booking.status}"
        )

    booking.status = "confirmed"

    db.commit()
    db.refresh(booking)

    return {
        "statusCode": 200,
        "message": "Booking accepted successfully",
        "response": {
            "booking_id": booking.id,
            "status": booking.status
        }
    }


# REJECT BOOKING
@routes.patch("/{booking_id}/reject")
def reject_booking(
    booking_id: int,
    db: Session = Depends(getDB),
    current_owner=Depends(getCurrentOwner)
):
    # Find booking
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Verify turf belongs to logged-in owner
    turf = db.query(models.Turf).filter(
        models.Turf.id == booking.turf_id,
        models.Turf.owner_id == current_owner.id
    ).first()

    if not turf:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage this booking"
        )

    # Only pending bookings can be rejected
    if booking.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Booking is already {booking.status}"
        )

    booking.status = "rejected"

    db.commit()
    db.refresh(booking)

    return {
        "statusCode": 200,
        "message": "Booking rejected successfully",
        "response": {
            "booking_id": booking.id,
            "status": booking.status
        }
    }

