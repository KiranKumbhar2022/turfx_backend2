
from pydantic import BaseModel, EmailStr
from typing import Optional


class OwnerManagementResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: str
    city: Optional[str] = None
    status: str
    is_banned: bool

    class Config:
        from_attributes = True


class OwnerPasswordResetRequest(BaseModel):
    new_password: str
