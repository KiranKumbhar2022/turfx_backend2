
from pydantic import BaseModel, Field

from app.database.database import getDB


class RejectOwnerRequest(BaseModel):
    rejection_reason: str = Field(
        min_length=5,
        max_length=250
    )