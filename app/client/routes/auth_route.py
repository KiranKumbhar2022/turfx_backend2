from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session
from app.client.schemas.auth_schema import UserSignUpReqBody,UserSignUpResponse,LoginReqBody,LoginResponse
from app.database.database import getDB
from app.client.controllers import auth_controllers 
from app.core.response import SuccessResponse

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
