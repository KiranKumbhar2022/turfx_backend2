from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.database import getDB

from app.owner.controllers import auth_controller

from app.owner.schemas.owner_auth_schema import (
    TurfOwnerLoginRequest,
    RefreshTokenRequest,
    OwnerResetPasswordRequest,
    OwnerVerifyEmailRequest
)
from app.core import security
from app.owner.models.owner_model import TurfOwnerModel
from app.core.config import setting 

routes = APIRouter(
    prefix="/turf-owner/auth",
    tags=["Turf Owner Authentication"]
)


# -------------------------
# OWNER SIGNUP API
# -------------------------
@routes.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=dict
)
def ownerSignUp(
    name: str = Form(...),
    mobile: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),

    profileImage: UploadFile = File(...),
    aadhaar_document: UploadFile = File(...),
    pan_document: UploadFile = File(...),
    licence_document: UploadFile = File(...),

    db: Session = Depends(getDB)
):
    return auth_controller.ownerSignUp(
        name=name,
        mobile=mobile,
        email=email,
        password=password,
        city=city,
        state=state,
        country=country,
        profileImage=profileImage,
        aadhaar_document=aadhaar_document,
        pan_document=pan_document,
        licence_document=licence_document,
        db=db
    )
# -------------------------
# OWNER LOGIN API
# -------------------------

@routes.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=dict
)
def ownerLogin(
    user: TurfOwnerLoginRequest,
    db: Session = Depends(getDB)
):

    return auth_controller.ownerLogin(
        email=user.email,
        password=user.password,
        db=db
    )

# VERIFY EMAIL
@routes.post(
    "/verify-email",
    status_code=status.HTTP_200_OK
)
def ownerVerifyEmail(
    request: OwnerVerifyEmailRequest,
    db: Session = Depends(getDB)
):
    return auth_controller.ownerVerifyEmail(
        email=request.email,
        db=db
    )


# RESET PASSWORD
@routes.post(
    "/reset-password",
    status_code=status.HTTP_200_OK
)
def ownerResetPassword(
    request: OwnerResetPasswordRequest,
    db: Session = Depends(getDB)
):
    return auth_controller.ownerResetPassword(
        email=request.email,
        new_password=request.new_password,
        confirm_password=request.confirm_password,
        db=db
    )


@routes.post("/refresh")
def refreshOwnerToken(
    request: RefreshTokenRequest,
    db: Session = Depends(getDB)
):

    # Verify refresh token
    payload = security.verifyRefreshToken(
        request.refresh_token
    )

    owner_id = int(payload["sub"])

    # Find owner
    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.id == owner_id
    ).first()

    if not owner:
        raise HTTPException(
            status_code=401,
            detail="Owner not found"
        )

    # Check banned owner
    if owner.is_banned:
        raise HTTPException(
            status_code=403,
            detail="Your account has been suspended by admin. Please contact support."
        )

    # Check approval status
    if owner.status != "approved":
        raise HTTPException(
            status_code=403,
            detail="Owner account is not approved"
        )

    # Generate new access token
    new_access_token = security.createAccessToken({
        "sub": str(owner.id),
        "role": "turf_owner"
    })

    return {
        "statusCode": 200,
        "message": "Access token refreshed successfully",
        "response": {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": setting.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    }


