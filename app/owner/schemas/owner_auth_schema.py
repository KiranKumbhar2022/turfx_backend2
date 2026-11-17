from pydantic import BaseModel, EmailStr, ConfigDict,Field
from datetime import datetime

class TurfOwnerSignupRequest(BaseModel):
    name: str
    mobile: str
    email: EmailStr
    password: str

    city: str
    state: str
    country: str


class TurfOwnerSignupResponse(BaseModel):
    id: int
    name: str
    mobile: str
    email: EmailStr
    city: str
    state: str
    country: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TurfOwnerLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TurfOwnerLoginResponse(BaseModel):
    statusCode: int
    message: str
    response: TurfOwnerSignupResponse
    access_token: str
    token_type: str 


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OwnerVerifyEmailRequest(BaseModel):
    email: EmailStr


class OwnerResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6, max_length=128)
    confirm_password: str = Field(min_length=6, max_length=128)