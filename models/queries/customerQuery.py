from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def customer(db: Session):
    return db.query(CustomerModel).first()
def listAllCustomers(db: Session,startDate:str,endDate:str,userId:str=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if userId:
            return db.query(CustomerModel).filter(CustomerModel.user_id == userId).filter(CustomerModel.created_at.between(start,end)).order_by(desc(CustomerModel.created_at)).all()
        return db.query(CustomerModel).filter(CustomerModel.created_at.between(start,end)).order_by(desc(CustomerModel.created_at)).all()
    

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