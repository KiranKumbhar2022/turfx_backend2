
from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminInfo(BaseModel):
    id: int
    name: str
    email: EmailStr


class AdminLoginResponse(BaseModel):
    statusCode: int
    message: str
    access_token: str
    token_type: str = "bearer"
    admin: AdminInfo
