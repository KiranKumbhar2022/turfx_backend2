from datetime import time,date
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PlayType(str, Enum):
    cricket = "Cricket"
    football = "Football"
    tennis = "Tennis"
    basketball = "Basketball"


class Weekday(int, Enum):
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6


class EquipmentIn(BaseModel):
    item: str = Field(min_length=1, max_length=80, examples=["Football"])
    price: float = Field(ge=0, examples=[50])

    @field_validator("item")
    @classmethod
    def strip_item(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Item name is required")
        return v


class EquipmentOut(EquipmentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ScheduleDayIn(BaseModel):
    day: Weekday
    is_open: bool = True
    open_time: time = time(6, 0)
    close_time: time = time(23, 0)

    @model_validator(mode="after")
    def check_times(self):
        if self.is_open and self.open_time >= self.close_time:
            raise ValueError("open_time must be before close_time")
        return self


class ScheduleDayOut(ScheduleDayIn):
    model_config = ConfigDict(from_attributes=True)


def default_schedule() -> list[ScheduleDayIn]:
    return [ScheduleDayIn(day=d) for d in Weekday]


class MediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    url: str


class TurfCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    price_per_hour: float = Field(gt=0)

    play_types: list[PlayType] = Field(min_length=1)
    rental_enabled: bool = False

    # NEW: Required location
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    latitude: float | None = None
    longitude: float | None = None

    equipment: list[EquipmentIn] = Field(default_factory=list)
    schedule: list[ScheduleDayIn] = Field(
        default_factory=default_schedule
    )

    @field_validator("name", "city", "state", "country")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @model_validator(mode="after")
    def check_all(self):
        if len({d.day for d in self.schedule}) != len(self.schedule):
            raise ValueError("Duplicate days in schedule")

        if not self.rental_enabled:
            self.equipment = []

        return self


class TurfUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    price_per_hour: float | None = Field(default=None, gt=0)
    play_types: list[PlayType] | None = Field(default=None, min_length=1)
    rental_enabled: bool | None = None
    equipment: list[EquipmentIn] | None = None
    schedule: list[ScheduleDayIn] | None = None


class TurfOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price_per_hour: float
    play_types: list[PlayType]
    rental_enabled: bool
    equipment: list[EquipmentOut]
    schedule: list[ScheduleDayOut]
    media: list[MediaOut]
    latitude: float | None = None
    longitude: float | None = None
    isFavorite: bool = False
    city: str
    state: str
    country: str

    @field_validator("play_types", mode="before")
    @classmethod
    def split_play_types(cls, v):
        return v.split(",") if isinstance(v, str) else v
    

class TurfListResponse(BaseModel):
    status_code: int
    message: str
    response: list[TurfOut]

class TurfDetailsResponse(BaseModel):
    status_code: int
    message: str
    response: TurfOut



class FavoriteTurfResponse(BaseModel):
    status_code: int
    message: str
    turf_id: int
    is_favorite: bool

class AvailableTimeSlot(BaseModel):
    start_time: time
    end_time: time
    is_booked: bool


class AvailableSlotsResponse(BaseModel):
    status_code: int
    message: str
    turf_id: int
    booking_date: date
    slot_duration: int
    available_slots: list[AvailableTimeSlot]



class BookingDecisionRequest(BaseModel):
    action: Literal["accept", "reject"]


class OwnerBookingRequestsResponse(BaseModel):
    status_code: int
    message: str
    response: list[dict]


class BookingDecisionResponse(BaseModel):
    status_code: int
    message: str
    response: dict
