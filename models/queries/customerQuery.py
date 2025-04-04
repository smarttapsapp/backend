from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def customer(db: Session):
    return db.query(CustomerModel).first()

def updateUserBvn(db: Session, userId: int,bvn:str):
    stmt = (update(CustomerModel)
            .where(CustomerModel.id == userId)
            .values(
                updated_at=datetime.now(),
                bvn= bvn,
                bvn_verified=True
                    )
            .execution_options(synchronize_session="fetch"))
    res = db.execute(statement=stmt)
    db.commit()
    return  res 