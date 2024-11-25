from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def notifications(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).join(UserNotification).join(CustomerModel).filter(CustomerModel.id==userId).all()
    return db.query(NotificationModel).all()
def notification(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def updateNotifications(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def updateNotification(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def deleteNotification(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def deleteNotifications(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()