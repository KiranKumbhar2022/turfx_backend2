from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.response import SuccessResponse


class UserSignUpReqBody(BaseModel):
    name: str
    userName: str
    email: EmailStr
    password: str
    mobileNo: str


class UserResponse(BaseModel):
    name: str
    username: str
    created_at: datetime
    email: EmailStr
    id: int
    phone: str | None
    updated_at: datetime
    profile_image: str | None
    token: str | None = None

    class Config:
        from_attributes = True


class UserSignUpResponse(SuccessResponse[UserResponse]):
    pass


class LoginReqBody(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(SuccessResponse[UserResponse]):
    access_token: str
    token_type: str