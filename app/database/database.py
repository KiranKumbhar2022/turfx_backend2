
from app.core.config import setting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
engine= create_engine(
    setting.DATABASE_URL
)

localSession=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):

    pass

def getDB():
    db=localSession()
    
    try:
        yield db

    finally :
        db.close()    
