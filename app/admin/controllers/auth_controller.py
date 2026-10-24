from fastapi import HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.owner.models.owner_model import TurfOwnerModel


# =========================================================
# GET ALL PENDING OWNERS
# =========================================================

def getPendingOwners(
    db: Session
):

    owners = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.status == "pending"
    ).order_by(
        TurfOwnerModel.created_at.desc()
    ).all()

    return {
        "statusCode": 200,

        "message": "Pending owners fetched successfully",

        "response": [
            {
                "id": owner.id,
                "name": owner.name,
                "mobile": owner.mobile,
                "email": owner.email,
                "city": owner.city,
                "state": owner.state,
                "country": owner.country,
                "aadhaar_document": owner.aadhaar_document,
                "pan_document": owner.pan_document,
                "licence_document": owner.licence_document,
                "status": owner.status,
                "created_at": (
                    owner.created_at.isoformat()
                    if owner.created_at
                    else None
                )
            }

            for owner in owners
        ]
    }


# =========================================================
# GET SINGLE OWNER
# =========================================================

def getOwnerById(
    owner_id: int,
    db: Session
):

    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.id == owner_id
    ).first()

    if not owner:

        return JSONResponse(
            status_code=404,
            content={
                "statusCode": 404,
                "message": "Owner not found"
            }
        )

    return {
        "statusCode": 200,

        "message": "Owner fetched successfully",

        "response": {
            "id": owner.id,
            "name": owner.name,
            "mobile": owner.mobile,
            "email": owner.email,
            "city": owner.city,
            "state": owner.state,
            "country": owner.country,
            "status": owner.status,
            "rejection_reason": owner.rejection_reason,
            "created_at": (
                owner.created_at.isoformat()
                if owner.created_at
                else None
            )
        }
    }


# =========================================================
# APPROVE OWNER
# =========================================================

def approveOwner(
    owner_id: int,
    db: Session
):

    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.id == owner_id
    ).first()

    if not owner:

        return JSONResponse(
            status_code=404,
            content={
                "statusCode": 404,
                "message": "Owner not found"
            }
        )

    # Already approved

    if owner.status == "approved":

        return JSONResponse(
            status_code=400,
            content={
                "statusCode": 400,
                "message": "Owner is already approved"
            }
        )

    owner.status = "approved"

    owner.rejection_reason = None

    db.commit()

    db.refresh(owner)

    return {
        "statusCode": 200,

        "message": "Owner approved successfully",

        "response": {
            "id": owner.id,
            "name": owner.name,
            "email": owner.email,
            "status": owner.status
        }
    }


# =========================================================
# REJECT OWNER
# =========================================================

def rejectOwner(
    owner_id: int,
    rejection_reason: str,
    db: Session
):

    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.id == owner_id
    ).first()

    if not owner:

        return JSONResponse(
            status_code=404,
            content={
                "statusCode": 404,
                "message": "Owner not found"
            }
        )

    # --------------------------------
    # Validate reason
    # --------------------------------

    rejection_reason = rejection_reason.strip()

    if not rejection_reason:

        return JSONResponse(
            status_code=400,
            content={
                "statusCode": 400,
                "message": "Rejection reason is required"
            }
        )

    # --------------------------------
    # Reject
    # --------------------------------

    owner.status = "rejected"

    owner.rejection_reason = rejection_reason

    db.commit()

    db.refresh(owner)

    return {
        "statusCode": 200,

        "message": "Owner rejected successfully",

        "response": {
            "id": owner.id,
            "name": owner.name,
            "email": owner.email,
            "status": owner.status,
            "rejection_reason": owner.rejection_reason
        }
    }