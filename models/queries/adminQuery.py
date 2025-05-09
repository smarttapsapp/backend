from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def admin(db: Session,username:str):
    return db.query(AdminModel).filter(AdminModel.email ==username).first()