from datetime import time

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Turf(Base):
    __tablename__ = "turfs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(
    ForeignKey("users.id"),
    nullable=True,
    index=True,
)

    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price_per_hour: Mapped[float] = mapped_column(Float)
    play_types: Mapped[str] = mapped_column(String(200))
    rental_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="turf",
        cascade="all, delete-orphan",
    )

    schedule: Mapped[list["ScheduleDay"]] = relationship(
        back_populates="turf",
        cascade="all, delete-orphan",
        order_by="ScheduleDay.day",
    )

    media: Mapped[list["Media"]] = relationship(
        back_populates="turf",
        cascade="all, delete-orphan",
    )

    bookings = relationship(
    "Booking",
    back_populates="turf",
)


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    turf_id: Mapped[int] = mapped_column(ForeignKey("turfs.id"))
    item: Mapped[str] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Float)

    turf: Mapped["Turf"] = relationship(back_populates="equipment")


class ScheduleDay(Base):
    __tablename__ = "schedule_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    turf_id: Mapped[int] = mapped_column(ForeignKey("turfs.id"))
    day: Mapped[int] = mapped_column(Integer)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    open_time: Mapped[time] = mapped_column(Time)
    close_time: Mapped[time] = mapped_column(Time)

    turf: Mapped["Turf"] = relationship(back_populates="schedule")


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    turf_id: Mapped[int] = mapped_column(ForeignKey("turfs.id"))
    kind: Mapped[str] = mapped_column(String(10))
    url: Mapped[str] = mapped_column(String(300))

    turf: Mapped["Turf"] = relationship(back_populates="media")
from sqlalchemy import (
    Integer,
    ForeignKey,
    UniqueConstraint,
)


class FavoriteTurf(Base):
    __tablename__ = "user_favorite_turfs"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "turf_id",
            name="uq_user_favorite_turf",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    turf_id: Mapped[int] = mapped_column(
        ForeignKey("turfs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )