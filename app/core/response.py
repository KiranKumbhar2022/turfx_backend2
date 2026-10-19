from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    statusCode: int
    message: str
    response: T | None = None