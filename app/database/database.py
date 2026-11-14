
from app.core.config import setting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Get database URL from environment/settings
database_url = setting.DATABASE_URL

# Convert PostgreSQL URL to psycopg 3 format
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )

elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

# SQLAlchemy engine
engine = create_engine(
    database_url,
    pool_pre_ping=True
)

# Database session
localSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


# Database dependency
def getDB():
    db = localSession()

    try:
        yield db

    finally:
        db.close()
