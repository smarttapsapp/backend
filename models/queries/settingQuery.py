from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def setting(db: Session):
    return db.query(SettingsModel).first()