from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import getDB
from app.owner.models.owner_model import TurfOwnerModel
from app.core import security


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/turf-owner/auth/login"
)


def getCurrentOwner(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(getDB)
):

    payload = security.verifyAccessToken(token)

    owner_id = int(payload["sub"])

    owner = db.query(TurfOwnerModel).filter(
        TurfOwnerModel.id == owner_id
    ).first()

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner not found"
        )

    if owner.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner account is not approved"
        )

    return owner