
import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "firebase-service-account.json"


def initialize_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if firebase_json:
        service_account_info = json.loads(firebase_json)
        cred = credentials.Certificate(service_account_info)

    elif SERVICE_ACCOUNT_FILE.exists():
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_FILE))

    else:
        raise FileNotFoundError(
            "Firebase credentials not found. "
            "Set FIREBASE_SERVICE_ACCOUNT_JSON in Render environment variables."
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
