
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

def query_bus_routes(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_no_type(db: Session, departure: str, arrival: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_departure(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_arrival(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()

def query_stations(db: Session):
    return db.query(StationModel).all()
def query_train_routes(db: Session, departure: str, arrival: str, seatType: str, takeOffTime: str):
    return db.query(RouteModel).all()