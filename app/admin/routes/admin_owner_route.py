from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.admin.schemas.admin_schemas import RejectOwnerRequest
from app.database.database import getDB
from app.admin.dependecy.admin_dependecy import get_current_admin


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from pwdlib import PasswordHash

from app.database.database import getDB
from app.owner.models.owner_model import TurfOwnerModel
from app.admin.schemas.admin_owner_schema import (
    OwnerPasswordResetRequest
)
from app.admin.controllers.auth_controller import (
    getPendingOwners,
    getOwnerById,
    approveOwner,
    rejectOwner
)


routes = APIRouter(
    prefix="/admin/owners",
    tags=["Admin - Owner Approval"]
)


# =========================================================
# GET PENDING OWNERS
# =========================================================

@routes.get("/pending")
def pendingOwners(
    db: Session = Depends(getDB)
):

    return getPendingOwners(db)


# =========================================================
# GET OWNER BY ID
# =========================================================

@routes.get("/{owner_id}")
def ownerDetails(
    owner_id: int,
    db: Session = Depends(getDB)
):

    return getOwnerById(
        owner_id,
        db
    )


# =========================================================
# APPROVE OWNER
# =========================================================

@routes.put("/{owner_id}/approve")
def approveOwnerRoute(
    owner_id: int,
    db: Session = Depends(getDB)
):

    return approveOwner(
        owner_id,
        db
    )


# =========================================================
# REJECT OWNER
# =========================================================

@routes.put("/{owner_id}/reject")
def rejectOwnerRoute(
    owner_id: int,
   request: RejectOwnerRequest,
    db: Session = Depends(getDB)
):

    return rejectOwner(
        owner_id,
        request.rejection_reason,
        db
    )







password_hash = PasswordHash.recommended()


# --------------------------------------------------
# GET ALL OWNERS + SEARCH + STATUS FILTER
# --------------------------------------------------

@routes.get("")
def get_all_owners(
    status: str = Query("ALL"),
    search: str = Query(""),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):
    query = select(TurfOwnerModel)

    # Search
    if search.strip():
        search_value = f"%{search.strip()}%"

        query = query.where(
            or_(
                TurfOwnerModel.name.ilike(search_value),
                TurfOwnerModel.email.ilike(search_value),
                TurfOwnerModel.mobile.ilike(search_value),
                TurfOwnerModel.city.ilike(search_value)
            )
        )

    # Status filter
    if status.upper() == "SUSPENDED":
        query = query.where(
            TurfOwnerModel.is_banned == True
        )

    elif status.upper() in ["PENDING", "APPROVED"]:
        query = query.where(
            TurfOwnerModel.is_banned == False,
            TurfOwnerModel.status == status.lower()
        )

    elif status.upper() != "ALL":
        raise HTTPException(
            status_code=400,
            detail="Invalid owner status"
        )

    # Total count before pagination
    owners = db.scalars(
        query.order_by(TurfOwnerModel.id.desc())
    ).all()

    total = len(owners)

    # Pagination
    paginated_owners = owners[skip:skip + limit]

    response = []

    for owner in paginated_owners:
        response.append({
            "id": owner.id,
            "name": owner.name,
            "email": owner.email,
            "mobile": owner.mobile,
            "city": owner.city,
            "status": (
                "suspended"
                if owner.is_banned
                else owner.status
            ),
            "is_banned": owner.is_banned
        })

    return {
        "statusCode": 200,
        "message": "Owners fetched successfully",
        "response": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "owners": response
        }
    }


# --------------------------------------------------
# BAN OWNER
# --------------------------------------------------

@routes.patch("/{owner_id}/ban")
def ban_owner(
    owner_id: int,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):
    owner = db.get(TurfOwnerModel, owner_id)

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Owner not found"
        )

    if owner.is_banned:
        raise HTTPException(
            status_code=400,
            detail="Owner is already suspended"
        )

    owner.is_banned = True

    db.commit()
    db.refresh(owner)

    return {
        "statusCode": 200,
        "message": "Owner suspended successfully",
        "response": {
            "id": owner.id,
            "name": owner.name,
            "status": "suspended",
            "is_banned": owner.is_banned
        }
    }


# --------------------------------------------------
# UNBAN OWNER
# --------------------------------------------------

@routes.patch("/{owner_id}/unban")
def unban_owner(
    owner_id: int,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):
    owner = db.get(TurfOwnerModel, owner_id)

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Owner not found"
        )

    if not owner.is_banned:
        raise HTTPException(
            status_code=400,
            detail="Owner is not suspended"
        )

    owner.is_banned = False

    db.commit()
    db.refresh(owner)

    return {
        "statusCode": 200,
        "message": "Owner activated successfully",
        "response": {
            "id": owner.id,
            "name": owner.name,
            "status": owner.status,
            "is_banned": owner.is_banned
        }
    }


# --------------------------------------------------
# RESET OWNER PASSWORD
# --------------------------------------------------

@routes.patch("/{owner_id}/reset-password")
def reset_owner_password(
    owner_id: int,
    request: OwnerPasswordResetRequest,
    db: Session = Depends(getDB),
    admin=Depends(get_current_admin)
):
    owner = db.get(TurfOwnerModel, owner_id)

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Owner not found"
        )

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    owner.hashed_password = password_hash.hash(
        request.new_password
    )

    db.commit()

    return {
        "statusCode": 200,
        "message": "Owner password reset successfully",
        "response": {
            "id": owner.id,
            "name": owner.name
        }
    }

