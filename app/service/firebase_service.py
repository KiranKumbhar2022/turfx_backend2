import firebase_admin

from firebase_admin import credentials
from firebase_admin import messaging

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SERVICE_ACCOUNT_FILE = (
    BASE_DIR / "firebase-service-account.json"
)


def initialize_firebase():

    if firebase_admin._apps:
        return

    cred = credentials.Certificate(
        str(SERVICE_ACCOUNT_FILE)
    )

    firebase_admin.initialize_app(cred)


def send_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: dict | None = None
):

    initialize_firebase()

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),

        data=data or {},

        token=fcm_token
    )

    response = messaging.send(message)

    return response