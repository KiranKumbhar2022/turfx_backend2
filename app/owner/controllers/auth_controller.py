
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.owner.models.owner_model import TurfOwnerModel
from app.core.owner import security
from fastapi.responses import JSONResponse


def ownerSignUp(
    name: str,
    mobile: str,
    email: str,
    password: str,
    city: str,
    state: str,
    country: str,
    profileImage: UploadFile,
    aadhaar_document: UploadFile,
    pan_document: UploadFile,
    licence_document: UploadFile,
    db: Session,
):
    existingEmail = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.email == email.strip().lower()
    ).first()

    if existingEmail:
        return JSONResponse(
            status_code=400,
            content={
                "statusCode": 400,
                "message": "Email already registered"
            }
        )

    existingMobile = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.mobile == mobile.strip()
    ).first()

    if existingMobile:
        return JSONResponse(
            status_code=400,
            content={
                "statusCode": 400,
                "message": "Mobile number already registered"
            }
        )

    uploaded_paths = []

    try:
        profile_image_path = security.save_document(
            profileImage,
            "profile"
        )
        uploaded_paths.append(profile_image_path)

        aadhaar_path = security.save_document(
            aadhaar_document,
            "aadhaar"
        )
        uploaded_paths.append(aadhaar_path)

        pan_path = security.save_document(
            pan_document,
            "pan"
        )
        uploaded_paths.append(pan_path)

        licence_path = security.save_document(
            licence_document,
            "licence"
        )
        uploaded_paths.append(licence_path)

        newOwner = TurfOwnerModel(
            name=name.strip(),
            mobile=mobile.strip(),
            email=email.strip().lower(),
            hashed_password=security.hashPassword(password),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),

            profileImage=profile_image_path,
            aadhaar_document=aadhaar_path,
            pan_document=pan_path,
            licence_document=licence_path,
            status="pending"
        )

        db.add(newOwner)
        db.commit()
        db.refresh(newOwner)

        return {
            "statusCode": 201,
            "message": (
                "Registration submitted successfully. "
                "Please wait for admin approval."
            ),
            "response": {
                "id": newOwner.id,
                "name": newOwner.name,
                "mobile": newOwner.mobile,
                "email": newOwner.email,
                "city": newOwner.city,
                "state": newOwner.state,
                "country": newOwner.country,
                "profileImage": newOwner.profileImage,
                "status": newOwner.status,
                "created_at": (
                    newOwner.created_at.isoformat()
                    if newOwner.created_at else None
                )
            }
        }

    except HTTPException:
        db.rollback()
        security.delete_uploaded_files(uploaded_paths)
        raise

    except IntegrityError as e:
        db.rollback()
        security.delete_uploaded_files(uploaded_paths)

        print("INTEGRITY ERROR:", repr(e))

        return JSONResponse(
            status_code=409,
            content={
                "statusCode": 409,
                "message": "Email or mobile number already registered"
            }
        )

    except Exception as e:
        db.rollback()
        security.delete_uploaded_files(uploaded_paths)

        print("OWNER SIGNUP ERROR:", repr(e))

        return JSONResponse(
            status_code=500,
            content={
                "statusCode": 500,
                "message": str(e)
            }
        )
    

def ownerLogin(
    email: str,
    password: str,
    db: Session
):

    ownerExist = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.email == email.lower()
    ).first()

    if not ownerExist:
        return JSONResponse(
            status_code=401,
            content={
                "message": "Invalid email or password"
            }
        )

    # Verify password
    if not security.verifyPassword(
        password,
        ownerExist.hashed_password
    ):
        return JSONResponse(
            status_code=401,
            content={
                "message": "Invalid email or password"
            }
        )

    # Check if owner is banned
    if ownerExist.is_banned:
        return JSONResponse(
            status_code=403,
            content={
                "statusCode": 403,
                "message": "Your account has been suspended by admin. Please contact support."
            }
        )

    # Check pending status
    if ownerExist.status == "pending":
        return JSONResponse(
            status_code=403,
            content={
                "message": "Your account is waiting for admin approval"
            }
        )

    # Check rejected status
    if ownerExist.status == "rejected":
        return JSONResponse(
            status_code=403,
            content={
                "message": "Your account has been rejected",
                "reason": ownerExist.rejection_reason
            }
        )

    # Check approved status
    if ownerExist.status != "approved":
        return JSONResponse(
            status_code=403,
            content={
                "message": "Your account is not active"
            }
        )

    # Generate access token
    accessToken = security.createAccessToken(
        data={
            "sub": str(ownerExist.id),
            "email": ownerExist.email,
            "role": "turf_owner"
        }
    )

    return {
        "statusCode": 200,
        "message": "Login successful",
        "response": {
            "id": ownerExist.id,
            "name": ownerExist.name,
            "mobile": ownerExist.mobile,
            "email": ownerExist.email,
            "city": ownerExist.city,
            "state": ownerExist.state,
            "country": ownerExist.country,
            "status": ownerExist.status
        },
        "access_token": accessToken,
        "token_type": "bearer"
    }


# STEP 1: VERIFY EMAIL
def ownerVerifyEmail(
    email: str,
    db: Session
):
    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.email == email.strip().lower()
    ).first()

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Email address is not registered"
        )

    if owner.is_banned:
        raise HTTPException(
            status_code=403,
            detail="Your account has been suspended"
        )

    return {
        "statusCode": 200,
        "message": "Email verified successfully",
        "response": {
            "email": owner.email
        }
    }


# STEP 2: RESET PASSWORD
def ownerResetPassword(
    email: str,
    new_password: str,
    confirm_password: str,
    db: Session
):
    if new_password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.email == email.strip().lower()
    ).first()

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Email address is not registered"
        )

    if owner.is_banned:
        raise HTTPException(
            status_code=403,
            detail="Your account has been suspended"
        )

    owner.hashed_password = security.hashPassword(
        new_password
    )

    db.commit()

    return {
        "statusCode": 200,
        "message": "Password changed successfully. Please login again."
    }
