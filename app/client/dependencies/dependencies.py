from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database.database import getDB
from app.core.config import setting as settings
from app.client.models.auth_model import clientAuthModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/user/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(getDB),
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
            )

        # Replace this with your actual client user model
        current_user = db.get(
            clientAuthModel,
            int(user_id),
        )

        if current_user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        return current_user

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )