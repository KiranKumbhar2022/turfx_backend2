
import os
import json
import firebase_admin

from firebase_admin import credentials
from firebase_admin import messaging

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SERVICE_ACCOUNT_FILE = (
    BASE_DIR / "firebase-service-account.json"
)


def initialize_firebase():

    # Prevent duplicate Firebase initialization
    if firebase_admin._apps:
        return firebase_admin.get_app()

    firebase_json = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    if firebase_json:

        # Render production credentials
        service_account_info = json.loads(firebase_json)

        cred = credentials.Certificate(
            service_account_info
        )

    else:

        # Local development credentials
        if not SERVICE_ACCOUNT_FILE.exists():
            raise FileNotFoundError(
                f"Firebase credentials not found: {SERVICE_ACCOUNT_FILE}"
            )

        cred = credentials.Certificate(
            str(SERVICE_ACCOUNT_FILE)
        )

    return firebase_admin.initialize_app(cred)


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
