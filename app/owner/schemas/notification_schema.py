from pydantic import BaseModel, Field


class FCMTokenRequest(BaseModel):

    fcm_token: str = Field(
        min_length=20,
        max_length=500
    )