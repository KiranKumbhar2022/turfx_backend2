from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status
)

from sqlalchemy.orm import Session

from app.database.database import getDB

from app.owner.controllers import auth_controller

from app.owner.schemas.owner_auth_schema import (
    TurfOwnerLoginRequest,
    TurfOwnerLoginResponse,
    TurfOwnerSignupResponse
)


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
    aadhaar_document=aadhaar_document,
    pan_document=pan_document,
    licence_document=licence_document,
    # fcm_token=fcm_token,
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