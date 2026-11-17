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
    user: LoginReqBody,
    db: Session = Depends(getDB)
):
    userExist = db.query(clientAuthModel).filter(
        clientAuthModel.email == user.email
    ).first()

    # 1. Check if user exists
    if not userExist:
        return JSONResponse(
            status_code=400,
            content={
                "statusCode": 400,
                "message": "Invalid email or Password"
            }
        )

    # 2. Verify password
    if not security.verifyPassword(
        user.password,
        userExist.hashed_password
    ):
        return JSONResponse(
            status_code=400,
            content={
                "statusCode": 400,
                "message": "Invalid email or Password"
            }
        )

    # 3. Check if customer is banned
    if userExist.is_banned:
        return JSONResponse(
            status_code=403,
            content={
                "statusCode": 403,
                "message": "Your account has been banned. Please contact support."
            }
        )

    # 4. Generate access token only if user is not banned
    accessToken = security.createAccessToken(data={
        "sub": str(userExist.id),
        "email": userExist.email
    })

    return {
        "statusCode": 200,
        "message": "Login successfully!",
        "response": userExist,
        "access_token": accessToken,
        "token_type": "bearer"
    }



def userVerifyEmail(
    email: str,
    db: Session
):
    user = db.query(clientAuthModel).filter(
        clientAuthModel.email == email.strip().lower()
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email address is not registered"
        )

    if user.is_banned:
        raise HTTPException(
            status_code=403,
            detail="Your account has been banned"
        )

    return {
        "statusCode": 200,
        "message": "Email verified successfully",
        "response": {
            "email": user.email
        }
    }


# ==================================
# RESET USER PASSWORD
# ==================================

def userResetPassword(
    email: str,
    new_password: str,
    confirm_password: str,
    db: Session
):
    # Check password match
    if new_password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    # Find user
    user = db.query(clientAuthModel).filter(
        clientAuthModel.email == email.strip().lower()
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email address is not registered"
        )

    if user.is_banned:
        raise HTTPException(
            status_code=403,
            detail="Your account has been banned"
        )

    try:
        # Hash new password
        user.hashed_password = security.hashPassword(
            new_password
        )

        db.commit()

        return {
            "statusCode": 200,
            "message": "Password changed successfully. Please login again."
        }

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to reset password"
        )