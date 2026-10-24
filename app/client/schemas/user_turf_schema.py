from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.owner.schemas.turf_schema import TurfOut 


class BookingEquipmentRequest(BaseModel):
    equipment_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)


class CheckoutRequest(BaseModel):
    turf_id: int = Field(gt=0)
    sport: str = Field(min_length=1)
    booking_date: date
    start_time: time
    end_time: time
    equipment: list[BookingEquipmentRequest] = Field(
        default_factory=list
    )


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    turf_id: int
    sport: str
    booking_date: date
    start_time: time
    end_time: time
    total_amount: float
    status: str
    payment_status: str
    created_at: datetime
    payable_amount: float = 0.0
    turf: TurfOut
    selected_equipment: list[dict] = Field(default_factory=list)


class BookingListResponse(BaseModel):
    status_code: int
    message: str
    response: list[BookingOut]


class BookingDetailsResponse(BaseModel):
    status_code: int
    message: str
    response: BookingOut



class CityLocationResponse(BaseModel):
    name: str
    state: str | None = None
    country: str | None = None
    latitude: float
    longitude: float


class CitySearchResponse(BaseModel):
    status_code: int
    message: str
    city: CityLocationResponse
