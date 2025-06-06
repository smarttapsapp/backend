from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update,case
from models.model import *
import logging

logger = logging.getLogger(__name__)

def countCustomers(db: Session):
    return db.query(CustomerModel).count()
def countActiveCustomers(db: Session):
    return db.query(CustomerModel).count()
def customersAnalytics(db: Session):
    row = db.query(
    func.count().label("total_customers"),
    func.sum(case((CustomerModel.account_status == "active", 1), else_=0)).label("active_customers"),
    func.sum(case((CustomerModel.account_status == "registration", 1), else_=0)).label("reg_customers"),
    func.sum(case((CustomerModel.account_status == "inactive", 1), else_=0)).label("inactive_customers"),
    func.sum(case((CustomerModel.account_status == "blocked", 1), else_=0)).label("blocked_customers"),
    func.sum(case((CustomerModel.account_status == "disabled", 1), else_=0)).label("disabled_customers")
).one()
    return dict(row._mapping)

def creditPaymentsAnalytics(db: Session):
    row = db.query(
    func.count().label("total_payment"),
    func.sum(PaymentModel.amount).label("total_amount"),
    func.sum(case((PaymentModel.status == "success", 1), else_=0)).label("successful_payments"),
    func.sum(case((PaymentModel.status == "failed", 1), else_=0)).label("failed_payments"),
    func.sum(case((PaymentModel.status == "initialize", 1), else_=0)).label("pending_payments"),
    func.sum(case((PaymentModel.status == "success", PaymentModel.amount), else_=0)).label("successful_amount"),
    func.sum(case((PaymentModel.status == "initialize", PaymentModel.amount), else_=0)).label("pending_amount"),
    func.sum(case((PaymentModel.status == "failed", PaymentModel.amount), else_=0)).label("failed_amount")
).filter(PaymentModel.payment_type == "CREDIT").one()
    return dict(row._mapping)
def debitPaymentsAnalytics(db: Session):
    row = db.query(
    func.count().label("total_payment"),
    func.sum(PaymentModel.amount).label("total_amount"),
    func.sum(case((PaymentModel.status == "success", 1), else_=0)).label("successful_payments"),
    func.sum(case((PaymentModel.status == "initialize", 1), else_=0)).label("pending_payments"),
    func.sum(case((PaymentModel.status == "failed", 1), else_=0)).label("failed_payments"),
    func.sum(case((PaymentModel.status == "success", PaymentModel.amount), else_=0)).label("successful_amount"),
    func.sum(case((PaymentModel.status == "initialize", PaymentModel.amount), else_=0)).label("pending_amount"),
    func.sum(case((PaymentModel.status == "failed", PaymentModel.amount), else_=0)).label("failed_amount")
).filter(PaymentModel.payment_type == "DEBIT").one()
    return dict(row._mapping)
def admin(db: Session,username:str):
    return db.query(AdminModel).filter(AdminModel.email ==username).first()
def getAllRole(db: Session,adminId:int=None):
    return db.query(RoleModel).order_by(desc(RoleModel.created_at)).all()
def getRole(db: Session,roleId:int=None):
    return db.query(RoleModel).filter(RoleModel.id ==roleId).first()
def getAllAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).order_by(desc(AdminModel.created_at)).all()
def getAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).filter(AdminModel.id ==adminId).first()

def getTrains(db: Session):
    return db.query(TrainModel).order_by(desc(TrainModel.created_at)).all()
def countTrains(db: Session):
    return db.query(TrainModel).count()
def getTrainsByBusiness(db: Session,adminId:int=None):
    return db.query(TrainModel).filter(TrainModel.route_id ==adminId).order_by(desc(TrainModel.created_at)).all()

def getBuses(db: Session):
    return db.query(BusModel).order_by(desc(BusModel.created_at)).all()
def countBuses(db: Session):
    return db.query(BusModel).count()
def getBusesByBusiness(db: Session,parkId:int=None):
    return db.query(BusModel).filter(BusModel.park_id ==parkId).order_by(desc(BusModel.created_at)).all()

def getParks(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(ParkModel).filter(ParkModel.created_at.between(start,end)).order_by(desc(ParkModel.created_at)).all()
    return db.query(ParkModel).order_by(desc(ParkModel.created_at)).all()

def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
def getAdmins(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
    return db.query(AdminModel).filter(AdminModel.created_at.between(start,end)).order_by(desc(AdminModel.created_at)).all()
def getTicketHistories(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(TicketModel).filter(TicketModel.admin_id == adminId).filter(TicketModel.created_at.between(start,end)).order_by(desc(TicketModel.created_at)).all()
    return db.query(TicketModel).order_by(desc(TicketModel.created_at)).all()
def getNotificationHistories(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(NotificationModel).filter(NotificationModel.admin_id == adminId).filter(NotificationModel.created_at.between(start,end)).order_by(desc(NotificationModel.created_at)).all()
    return db.query(NotificationModel).order_by(desc(NotificationModel.created_at)).all()