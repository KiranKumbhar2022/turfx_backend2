
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
        "status": newOwner.status,
        "created_at": newOwner.created_at
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
                "message":"Invalid email or password"
            }
        )

    if not security.verifyPassword(
        password,
        ownerExist.hashed_password
    ):
        return JSONResponse(
            status_code=401,
            content={
                "message":"Invalid email or password"
            }
        )

    if ownerExist.status == "pending":
        return JSONResponse(
            status_code=403,
            content={
                "message":"Your account is waiting for admin approval"
            }
        )

    if ownerExist.status == "rejected":
        return JSONResponse(
            status_code=403,
            content={
                "message":"Your account has been rejected",
                "reason": ownerExist.rejection_reason
            }
        )

    if ownerExist.status != "approved":
        return JSONResponse(
            status_code=403,
            content={
                "message":"Your account is not active"
            }
        )

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
