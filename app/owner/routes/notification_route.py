from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import getDB
from app.owner.models.owner_model import TurfOwnerModel
from  app.owner.dependencies.dependecies import getCurrentOwner
from app.owner.schemas.notification_schema import (
    FCMTokenRequest
)

from app.owner.controllers import notification_controller


routes = APIRouter(
    prefix="/turf-owner/notification",
    tags=["Turf Owner Notifications"]
)


@routes.post("/fcm-token")
def registerFCMToken(
    request: FCMTokenRequest,

    owner: TurfOwnerModel =  Depends(getCurrentOwner),

    db: Session = Depends(getDB)
):

    return notification_controller.saveFCMToken(
        owner=owner,
        fcm_token=request.fcm_token,
        db=db
    )