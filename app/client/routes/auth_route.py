from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session
from app.client.schemas.auth_schema import UserSignUpReqBody,UserSignUpResponse,LoginReqBody,LoginResponse,UserVerifyEmailRequest,UserResetPasswordRequest
from app.database.database import getDB
from app.client.controllers import auth_controllers

routes=APIRouter(prefix="/user/auth")

@routes.post("/register",status_code=status.HTTP_200_OK, response_model=UserSignUpResponse)
def userSignUp(
    user:UserSignUpReqBody,
    db:Session=Depends(getDB),
):
    return auth_controllers.clientSignUp(user=user,db=db)

@routes.post("/login",status_code=status.HTTP_200_OK,response_model=LoginResponse)
def userLogin(  
    user:LoginReqBody,
    db:Session=Depends(getDB)
):
    return auth_controllers.login(user=user,db=db)


# ==================================
# VERIFY USER EMAIL
# ==================================

@routes.post(
    "/verify-email",
    status_code=status.HTTP_200_OK
)
def userVerifyEmail(
    request: UserVerifyEmailRequest,
    db: Session = Depends(getDB)
):
    return auth_controllers.userVerifyEmail(
        email=request.email,
        db=db
    )


# ==================================
# RESET USER PASSWORD
# ==================================

@routes.post(
    "/reset-password",
    status_code=status.HTTP_200_OK
)
def userResetPassword(
    request: UserResetPasswordRequest,
    db: Session = Depends(getDB)
):
    return auth_controllers.userResetPassword(
        email=request.email,
        new_password=request.new_password,
        confirm_password=request.confirm_password,
        db=db
    )

