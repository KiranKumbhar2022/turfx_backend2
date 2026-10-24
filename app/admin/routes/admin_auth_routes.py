from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.admin.schemas.admin_schemas import RejectOwnerRequest
from app.database.database import getDB

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