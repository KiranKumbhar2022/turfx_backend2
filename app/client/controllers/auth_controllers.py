from app.client.schemas.auth_schema import UserSignUpReqBody,UserSignUpResponse,LoginReqBody,LoginResponse
from app.database.database import getDB
from sqlalchemy.orm import Session
from fastapi import Depends,HTTPException
from app.client.models.auth_model import clientAuthModel
from app.core import security 
from fastapi.responses import JSONResponse


def clientSignUp(
      user:UserSignUpReqBody,
      db: Session=Depends(getDB)
):
    existingEmail = db.query(clientAuthModel).filter(
        clientAuthModel.email == user.email
    ).first()

    username = security.generateUniqueUsername(user.name, db)

    if existingEmail:
        return JSONResponse(
        status_code=400,
        content={
            "statusCode": 400,
            "message": "this email already exist"
        }
        )


    newUser = clientAuthModel(
        name=user.name,
        username=username,
        email=user.email,
        phone=user.mobileNo,
        hashed_password=security.hashPassword(user.password),
        temp_token=security.generateRandomToken()
    )

    db.add(newUser)
    db.commit()
    db.refresh(newUser)

    return {
        "statusCode": 200,
        "message": "User is created!!",
        "response": newUser
    }


def login(
    user:LoginReqBody,
    db: Session=Depends(getDB)):
    userExist=db.query(clientAuthModel).filter(clientAuthModel.email == user.email).first()

    if not userExist:
        return JSONResponse(
        status_code=400,
        content={
            "statusCode": 400,
            "message": "Invalid email or Password"
        }
        )
    if not security.verifyPassword(user.password,userExist.hashed_password):
        return JSONResponse(
        status_code=400,
        content={
            "statusCode": 400,
            "message": "Invalid email or Password"
        }
        )
    
    accessToken=security.createAccessToken(data={
        "sub":str(userExist.id),
        "email":userExist.email
    })
    
    return {
    "statusCode": 200,
    "message": "login successfully!!!",
    "response": userExist,
    "access_token": accessToken,
    "token_type": "bearer"
    }





