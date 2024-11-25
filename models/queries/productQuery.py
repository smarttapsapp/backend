
from sqlalchemy.orm import Session
from models.model import *
import logging

logger = logging.getLogger(__name__)

def get_all_bill(db: Session):
    return db.query(ProductModel).all()


def get_single_bill_by_id(db: Session, id: int):
    return db.query(ProductModel).filter(ProductModel.id == id).first()


def get_all_biller(db: Session):
    return db.query(ProductTypeModel).all()


def get_single_biller_by_id(db: Session, id: int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.id == id).first()


def get_single_biller_by_billerId(db: Session, billerId: str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerId == billerId).first()
