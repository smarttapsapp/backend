
from sqlalchemy.orm import Session
from models.model import *
import logging

logger = logging.getLogger(__name__)

def getAll(db: Session):
    return db.query(TransactionModel).all()

def getAllByUser(db: Session, userId:int,start:DateTime,end:DateTime,transType:str):
    return db.query(TransactionModel).filter(TransactionModel.user_id==userId).all()

def getOne(db: Session, id: int):
    return db.query(TransactionModel).first()

def getOneById(db: Session, id: int):
    return db.query(TransactionModel).filter(TransactionModel.id == id).first()
