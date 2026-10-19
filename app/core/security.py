
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from app.core.config import setting
from jose import jwt
from app.client.models.auth_model import clientAuthModel
import re
from sqlalchemy.orm import Session
import random
from jose import JWTError
from fastapi import HTTPException, status

passwordHash=PasswordHash.recommended()

def hashPassword(password:str):
    return passwordHash.hash(password)

def verifyPassword(password:str, hashPassword):
    return passwordHash.verify(password,hashPassword)

def createAccessToken(data:dict):
    toEncoded=data.copy()
    expire= datetime.now(timezone.utc) + timedelta(minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES)

    toEncoded.update({"exp":expire})

    enCodedJwtToken=jwt.encode(toEncoded,setting.SECRET_KEY,algorithm=setting.ALGORITHM)
    return enCodedJwtToken

def generateUniqueUsername(
    name: str,
    db: Session
) -> str:

    username = name.lower().strip()
    username = re.sub(r'[^a-z0-9]+', '_', username)
    username = username.strip('_')
    if not username:
        username = "user"
    username = f"{username}{random.randint(1000, 9999)}"
    while db.query(clientAuthModel).filter(
        clientAuthModel.username == username
    ).first():

        username = f"{name.lower().replace(' ', '_')}{random.randint(1000, 9999)}"

    return username

def generateRandomToken():
    token = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=30))
    return token


def verifyAccessToken(token: str) -> dict:

    try:
        payload = jwt.decode(
            token,
            setting.SECRET_KEY,
            algorithms=[setting.ALGORITHM]
        )

        owner_id = payload.get("sub")
        role = payload.get("role")

        if owner_id is None or role != "turf_owner":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid owner token"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

