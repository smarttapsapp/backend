from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.util import get_setting
from models.model import Base


engine = create_engine(
    get_setting().db_url,
    #echo=True,
    pool_pre_ping=True,
    # SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_size=50, max_overflow=120
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base.metadata.drop_all(bind=engine)
# engine.dispose()
Base.metadata.create_all(bind=engine)
"""
async def get_db():
    async with SessionLocal() as db:
        yield db
"""
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
