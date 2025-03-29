
from sqlalchemy.orm import Session
from models.model import *
import logging

logger = logging.getLogger(__name__)

def querySender(db:Session,walletAccount:str):
    return db.query(AccountModel).filter(AccountModel.walletAccount == walletAccount).first()
def queryLatestRecordByAmount(db:Session,amount:str):
    return db.query(PaymentModel).filter(PaymentModel.amount == amount).first()
def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
def create_payment(db: Session, payment: PaymentModel):
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
def getPaymentByReference(db: Session, reference: str):
    return db.query(PaymentModel).filter(PaymentModel.reference == reference).first()
def create_card(db: Session, card: CardsModel):
    db.add(card)
    db.commit()
    db.refresh(card)
    return card
def getCardByLast4(db: Session, last4: str):
    return db.query(CardsModel).filter(CardsModel.last4 == last4).first()

def getPaymentHistories(db: Session,userId:int,start:DateTime,end:DateTime,transType:str):
    return db.query(PaymentModel).filter(PaymentModel.user_id == userId).all()

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

def query_bus_routes(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_no_type(db: Session, departure: str, arrival: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_departure(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_arrival(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
