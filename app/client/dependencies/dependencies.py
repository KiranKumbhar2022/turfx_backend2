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

        current_user = db.get(
            clientAuthModel,
            int(user_id),
        )

        if current_user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        # Check whether customer is banned
        if current_user.is_banned:
            raise HTTPException(
                status_code=403,
                detail="Your account has been banned. Please contact support.",
            )

        return current_user

    except HTTPException:
        raise

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
