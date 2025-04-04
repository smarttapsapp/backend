from sqlalchemy.orm import Session
from models.model import *
import logging

logger = logging.getLogger(__name__)

def setting(db: Session):
    return db.query(SettingsModel).first()