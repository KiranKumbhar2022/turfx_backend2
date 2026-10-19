from pydantic import BaseModel, EmailStr, ConfigDict
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