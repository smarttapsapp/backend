from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.util import get_setting
from models.model import Base


engine = create_engine(
    get_setting().db_url,pool_pre_ping=True,pool_size=20, max_overflow=10,pool_recycle=1800,pool_timeout=30,connect_args={
        "buffered":           True,    # fetch results into memory immediately
        "consume_results":    True,    # auto-discard unread results
        "connection_timeout": 30,      # TCP connect timeout
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
celery_engine = create_engine(
    get_setting().db_url,
    pool_pre_ping=True,
    pool_size=5,             # smaller — background tasks need fewer connections
    max_overflow=5,
    pool_recycle=1800,
    pool_timeout=10,         # fail faster — don't hold up the task queue
    connect_args={
        "buffered":        True,
        "consume_results": True,
    },
)
CelerySessionLocal = sessionmaker(
    bind=celery_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

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
