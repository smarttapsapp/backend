from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def admin(db: Session,username:str):
    return db.query(AdminModel).filter(AdminModel.email ==username).first()
def getAllAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).order_by(desc(AdminModel.created_at)).all()
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