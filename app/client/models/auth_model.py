from sqlalchemy import String,Boolean,Integer,Enum,DateTime
from app.database.database import Base
from sqlalchemy.orm import Mapped,mapped_column,relationship
from datetime import datetime

class clientAuthModel(Base):
    
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
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

    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
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

    profile_image: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True
    )
    temp_token: Mapped[str | None] = mapped_column(
    String(30),
    nullable=True
    )

