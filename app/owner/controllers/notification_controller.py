from sqlalchemy.orm import Session

from app.owner.models.owner_model import TurfOwnerModel


def saveFCMToken(
    owner: TurfOwnerModel,
    fcm_token: str,
    db: Session
):
    try:
        owner.fcm_token = fcm_token

        db.commit()
        db.refresh(owner)

        return {
            "statusCode": 200,
            "message": "FCM token registered successfully"
        }

    except Exception:
        db.rollback()
        raise