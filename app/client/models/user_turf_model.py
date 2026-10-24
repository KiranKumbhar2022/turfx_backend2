from sqlalchemy import (
    Column, Integer, String, Date, Time, Float,
    DateTime, ForeignKey, func
)
from app.database.database import Base  
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    turf_id = Column(
        Integer,
        ForeignKey("turfs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sport = Column(String, nullable=False)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    total_amount = Column(Float, nullable=False)
    status = Column(
        String,
        nullable=False,
        default="pending",
        index=True,
    )
    payment_status = Column(
        String,
        nullable=False,
        default="unpaid",
    )

    selected_equipment = Column(
        JSON,
        nullable=False,
        default=list,
    )

    # Relationship with Turf
    turf = relationship(
        "Turf",
        back_populates="bookings",
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )