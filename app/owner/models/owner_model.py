from sqlalchemy import String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.database.database import Base


class TurfOwnerModel(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    profileImage: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    mobile: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    aadhaar_document: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    pan_document: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    licence_document: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    fcm_token: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True
    )
    is_banned: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False
)
reset_token_hash: Mapped[str | None] = mapped_column(
    String(255),
    nullable=True
)

reset_token_expires_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
)