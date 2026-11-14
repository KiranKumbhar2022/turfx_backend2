
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from app.database.database import getDB
from app.client.models.auth_model import clientAuthModel
from app.client.models.user_turf_model import Booking
from app.admin.dependecy.admin_dependecy import get_current_admin


routes = APIRouter(
    prefix="/admin/users",
    tags=["Admin User Management"]
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(
        min_length=8,
        max_length=72
    )


# ==========================================
# HELPER FUNCTION
# ==========================================

def get_customer_by_id(
    user_id: int,
    db: Session
):
    customer = db.query(clientAuthModel).filter(
        clientAuthModel.id == user_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


def customer_response(customer, total_bookings=0):

    return {
        "id": customer.id,
        "name": customer.name,
        "username": customer.username,
        "email": customer.email,
        "phone": customer.phone,
        "profile_image": customer.profile_image,
        "role": "customer",
        "total_bookings": total_bookings,
        "status": (
            "banned" if customer.is_banned else "active"
        ),
        "created_at": customer.created_at,
        "updated_at": customer.updated_at
    }


# ==========================================
# GET ALL CUSTOMERS
# ==========================================

@routes.get("")
def get_all_customers(
    search: str = Query("", description="Search customers"),
    status: str = Query(
        "all",
        description="all, active, banned"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),

    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    query = db.query(clientAuthModel)

    # SEARCH
    if search.strip():

        search_value = f"%{search.strip()}%"

        query = query.filter(
            or_(
                clientAuthModel.name.ilike(search_value),
                clientAuthModel.username.ilike(search_value),
                clientAuthModel.email.ilike(search_value),
                clientAuthModel.phone.ilike(search_value)
            )
        )

    # STATUS FILTER
    if status.lower() == "active":

        query = query.filter(
            clientAuthModel.is_banned == False
        )

    elif status.lower() == "banned":

        query = query.filter(
            clientAuthModel.is_banned == True
        )

    elif status.lower() != "all":

        raise HTTPException(
            status_code=400,
            detail="Invalid status. Use all, active or banned"
        )

    # TOTAL COUNT
    total = query.count()

    # FETCH CUSTOMERS
    customers = (
        query
        .order_by(clientAuthModel.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # BOOKING COUNTS
    user_ids = [customer.id for customer in customers]

    booking_counts = {}

    if user_ids:

        results = (
            db.query(
                Booking.user_id,
                func.count(Booking.id).label("total")
            )
            .filter(Booking.user_id.in_(user_ids))
            .group_by(Booking.user_id)
            .all()
        )

        booking_counts = {
            user_id: total
            for user_id, total in results
        }

    users = []

    for customer in customers:

        users.append(
            customer_response(
                customer,
                booking_counts.get(customer.id, 0)
            )
        )

    return {
        "statusCode": 200,
        "message": "Customers fetched successfully",
        "response": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": users
        }
    }


# ==========================================
# GET CUSTOMER DETAILS
# ==========================================

@routes.get("/{user_id}")
def get_customer_details(
    user_id: int,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    customer = get_customer_by_id(user_id, db)

    total_bookings = (
        db.query(func.count(Booking.id))
        .filter(Booking.user_id == user_id)
        .scalar()
    ) or 0

    return {
        "statusCode": 200,
        "message": "Customer details fetched successfully",
        "response": customer_response(
            customer,
            total_bookings
        )
    }


# ==========================================
# BAN CUSTOMER
# ==========================================

@routes.patch("/{user_id}/ban")
def ban_customer(
    user_id: int,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    customer = get_customer_by_id(user_id, db)

    if customer.is_banned:

        raise HTTPException(
            status_code=400,
            detail="Customer is already banned"
        )

    customer.is_banned = True

    db.commit()
    db.refresh(customer)

    return {
        "statusCode": 200,
        "message": "Customer banned successfully",
        "response": {
            "id": customer.id,
            "status": "banned"
        }
    }


# ==========================================
# UNBAN CUSTOMER
# ==========================================

@routes.patch("/{user_id}/unban")
def unban_customer(
    user_id: int,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    customer = get_customer_by_id(user_id, db)

    if not customer.is_banned:

        raise HTTPException(
            status_code=400,
            detail="Customer is not banned"
        )

    customer.is_banned = False

    db.commit()
    db.refresh(customer)

    return {
        "statusCode": 200,
        "message": "Customer unbanned successfully",
        "response": {
            "id": customer.id,
            "status": "active"
        }
    }


# ==========================================
# RESET CUSTOMER PASSWORD
# ==========================================

@routes.patch("/{user_id}/reset-password")
def reset_customer_password(
    user_id: int,
    request: ResetPasswordRequest,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):

    customer = get_customer_by_id(user_id, db)

    customer.hashed_password = pwd_context.hash(
        request.new_password
    )

    db.commit()
    db.refresh(customer)

    return {
        "statusCode": 200,
        "message": "Customer password reset successfully",
        "response": {
            "id": customer.id,
            "message": "Password updated successfully"
        }
    }
