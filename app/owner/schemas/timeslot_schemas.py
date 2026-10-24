from datetime import date, time
from pydantic import BaseModel

class AvailableTimeSlot(BaseModel):
    start_time: time
    end_time: time


class AvailableSlotsResponse(BaseModel):
    status_code: int
    message: str
    turf_id: int
    booking_date: date
    slot_duration: int
    available_slots: list[AvailableTimeSlot]