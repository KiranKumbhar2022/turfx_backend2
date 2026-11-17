import csv
from io import StringIO
from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, cast, String

from app.database.database import getDB

# Existing models
from app.client.models.auth_model import clientAuthModel
from app.owner.models.owner_model import TurfOwnerModel

# from app.models.turf_model import Turf
from app.owner.models.turf_model import Turf as TurfModel
from app.client.models.user_turf_model import Booking

# Existing admin authentication
from app.admin.dependecy.admin_dependecy import get_current_admin


routes = APIRouter(
    prefix="/admin/bookings",
    tags=["Admin - Booking Oversight"]
)


# ==================================================
# COMMON BOOKING QUERY
# ==================================================

def getBookingQuery(
    db: Session,
    search: str = "",
    booking_status: str = "all",
    city: str = "all",
    today: bool = False
):

    query = (
        db.query(
            Booking,

            clientAuthModel.name.label("customer_name"),
            clientAuthModel.email.label("customer_email"),
            clientAuthModel.phone.label("customer_mobile"),

            TurfModel.name.label("turf_name"),
            TurfModel.city.label("city"),

            TurfOwnerModel.name.label("owner_name")
        )

        .join(
            clientAuthModel,
            clientAuthModel.id == Booking.user_id
        )

        .join(
            TurfModel,
            TurfModel.id == Booking.turf_id
        )

        .join(
            TurfOwnerModel,
            TurfOwnerModel.id == TurfModel.owner_id
        )
    )

    # SEARCH
    if search.strip():

        search_value = f"%{search.strip()}%"

        booking_code = func.concat(
            "BK-",
            cast(Booking.id, String)
        )

        query = query.filter(
            or_(
                cast(Booking.id, String).ilike(search_value),
                booking_code.ilike(search_value),
                clientAuthModel.name.ilike(search_value),
                clientAuthModel.email.ilike(search_value),
                clientAuthModel.phone.ilike(search_value),
                TurfModel.name.ilike(search_value),
                TurfOwnerModel.name.ilike(search_value),
                TurfModel.city.ilike(search_value)
            )
        )

    # STATUS FILTER
    if booking_status.lower() != "all":

        query = query.filter(
            func.lower(Booking.status) == booking_status.lower()
        )

    # CITY FILTER
    if city.lower() != "all":

        query = query.filter(
            func.lower(TurfModel.city) == city.strip().lower()
        )

    # TODAY FILTER
    if today:

        query = query.filter(
            Booking.booking_date == date.today()
        )

    return query

# ==================================================
# GET ALL BOOKINGS
# ==================================================

@routes.get("")
def getAllBookings(

    search: str = Query(""),

    booking_status: str = Query(
        "all",
        alias="status"
    ),

    city: str = Query("all"),

    today: bool = Query(False),

    skip: int = Query(0, ge=0),

    limit: int = Query(50, ge=1, le=100),

    db: Session = Depends(getDB),

    admin=Depends(get_current_admin)

):

    query = getBookingQuery(
        db=db,
        search=search,
        booking_status=booking_status,
        city=city,
        today=today
    )

    # Total count
    total = query.count()

    # Pagination
    results = (
        query
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    bookings = []

    for row in results:

        booking = row[0]

        bookings.append({

            "id": booking.id,

            "booking_code": f"BK-{booking.id}",

            "customer_name": row.customer_name,

            "customer_email": row.customer_email,

            "customer_mobile": row.customer_mobile,

            "turf_name": row.turf_name,

            "owner_name": row.owner_name,

            "city": row.city,

            "sport": booking.sport,

            "booking_date": str(
                booking.booking_date
            ),

            "start_time": str(
                booking.start_time
            ),

            "end_time": str(
                booking.end_time
            ),

            "total_amount": booking.total_amount,

            "status": booking.status,

            "payment_status": booking.payment_status,
            "booking_date":booking.booking_date

        })

    return {

        "statusCode": 200,

        "message": "Bookings fetched successfully",

        "response": {

            "total": total,

            "skip": skip,

            "limit": limit,

            "bookings": bookings

        }

    }


# ==================================================
# FORCE CANCEL BOOKING
# ==================================================

@routes.patch("/{booking_id}/force-cancel")
def forceCancelBooking(

    booking_id: int,

    db: Session = Depends(getDB),

    admin=Depends(get_current_admin)

):

    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Already cancelled
    if booking.status.lower() == "cancelled":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled"
        )

    # Completed booking
    if booking.status.lower() == "completed":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed booking cannot be cancelled"
        )

    # Only pending and confirmed bookings
    if booking.status.lower() not in [
        "pending",
        "confirmed"
    ]:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking cannot be cancelled"
        )

    # Admin force cancellation
    booking.status = "cancelled"

    # IMPORTANT:
    # Do not modify payment_status.
    # No refund will be initiated.

    db.commit()

    db.refresh(booking)

    return {

        "statusCode": 200,

        "message": "Booking cancelled successfully by admin",

        "response": {

            "id": booking.id,

            "booking_code": f"BK-{booking.id}",

            "status": booking.status,

            "payment_status": booking.payment_status

        }

    }


# ==================================================
# EXPORT BOOKINGS CSV
# ==================================================

@routes.get("/export")
def exportBookingsCSV(

    search: str = Query(""),

    booking_status: str = Query(
        "all",
        alias="status"
    ),

    city: str = Query("all"),

    today: bool = Query(False),

    db: Session = Depends(getDB),

    admin=Depends(get_current_admin)

):

    query = getBookingQuery(
        db=db,
        search=search,
        booking_status=booking_status,
        city=city,
        today=today
    )

    results = (
        query
        .order_by(Booking.created_at.desc())
        .all()
    )

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow([

        "Booking ID",
        "Customer",
        "Customer Email",
        "Mobile",
        "Turf",
        "Owner",
        "City",
        "Sport",
        "Booking Date",
        "Start Time",
        "End Time",
        "Amount",
        "Status",
        "Payment Status"

    ])

    for row in results:

        booking = row[0]

        writer.writerow([

            f"BK-{booking.id}",

            row.customer_name,

            row.customer_email,

            row.customer_mobile,

            row.turf_name,

            row.owner_name,

            row.city,

            booking.sport,

            booking.booking_date,

            booking.start_time,

            booking.end_time,

            booking.total_amount,

            booking.status,

            booking.payment_status

        ])

    output.seek(0)

    return StreamingResponse(

        iter([output.getvalue()]),

        media_type="text/csv",

        headers={

            "Content-Disposition":
            "attachment; filename=turf_bookings.csv"

        }

    )


# ==================================================
# GET AVAILABLE CITIES
# ==================================================

@routes.get("/cities")
def getBookingCities(

    db: Session = Depends(getDB),

    admin=Depends(get_current_admin)

):

    cities = (

        db.query(TurfModel.city)

        .join(
            Booking,
            Booking.turf_id == TurfModel.id
        )

        .filter(
            TurfModel.city.isnot(None)
        )

        .distinct()

        .order_by(TurfModel.city)

        .all()

    )

    return {

        "statusCode": 200,

        "message": "Cities fetched successfully",

        "response": [
            city[0] for city in cities
        ]

    }



@routes.get("/debug")
def debugBookings(
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    total_bookings = db.query(Booking).count()

    user_join = (
        db.query(Booking)
        .join(
            clientAuthModel,
            clientAuthModel.id == Booking.user_id
        )
        .count()
    )

    turf_join = (
        db.query(Booking)
        .join(
            clientAuthModel,
            clientAuthModel.id == Booking.user_id
        )
        .join(
            TurfModel,
            TurfModel.id == Booking.turf_id
        )
        .count()
    )

    owner_join = (
        db.query(Booking)
        .join(
            clientAuthModel,
            clientAuthModel.id == Booking.user_id
        )
        .join(
            TurfModel,
            TurfModel.id == Booking.turf_id
        )
        .join(
            TurfOwnerModel,
            TurfOwnerModel.id == TurfModel.owner_id
        )
        .count()
    )

    return {
        "statusCode": 200,
        "message": "Booking database diagnostics",
        "response": {
            "total_bookings": total_bookings,
            "after_user_join": user_join,
            "after_turf_join": turf_join,
            "after_owner_join": owner_join
        }
    }



@routes.get("/debug-owner-join")
def debugOwnerJoin(
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    results = (
        db.query(
            Booking.id.label("booking_id"),
            TurfModel.id.label("turf_id"),
            TurfModel.owner_id.label("turf_owner_id"),
            TurfOwnerModel.id.label("matched_owner_id"),
            TurfOwnerModel.name.label("owner_name")
        )
        .join(
            TurfModel,
            TurfModel.id == Booking.turf_id
        )
        .outerjoin(
            TurfOwnerModel,
            TurfOwnerModel.id == TurfModel.owner_id
        )
        .all()
    )

    return {
        "statusCode": 200,
        "message": "Owner join diagnostic",
        "response": [
            {
                "booking_id": row.booking_id,
                "turf_id": row.turf_id,
                "turf_owner_id": row.turf_owner_id,
                "matched_owner_id": row.matched_owner_id,
                "owner_name": row.owner_name
            }
            for row in results
        ]
    }



