
import logging
from sqlalchemy.orm import Session
from models.model import *
from schemas.notification import NotificationsResponse
from models.queries import notificationQuery,queries
from datetime import datetime,timedelta
from schemas import otp
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.admin import Admin
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)


def getNotifications(db: Session,userId:int):
    notifications = queries.notifications(db=db,userId=userId)
    logger.info(notifications)
    return NotificationsResponse(statusCode="200",statusDescription=SUCCESS,data=notifications)
def getNotification(db: Session,userId:int,notificationId:int):
    notifications = queries.notifications(db=db,userId=userId)
    logger.info(notifications)
    return notifications
def readNotification(db: Session,response:Response,userId:int,notificationId:int):
    notification = queries.queryNotification(db=db,userId=userId,notificationId=notificationId)
    logger.info(notification)
    if notification:
        notification.isRead = True
        notification.updated_at = datetime.now()
        updated = queries.create(db=db,model=notification)
        if updated:
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
def readNotifications(db: Session,userId:int,notificationId:int):
    notifications = queries.notifications(db=db,userId=userId)
    logger.info(notifications)
    return notifications
def deleteNotification(db: Session,response:Response,userId:int,notificationId:int):
    deleted = queries.deleteNotification(db=db,userId=userId,notificationId=notificationId)
    logger.info(deleted)
    if deleted:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)

def createNotification(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        payload: CustomerRequest,
        background_task: BackgroundTasks,):
    try:
        user = queries.getCheckAdmin(db=db,username=payload.email)
        if user:
            response.status_code = status.HTTP_302_FOUND
            return BaseResponse(
                    statusCode=str(status.HTTP_302_FOUND),
                    statusDescription=ALREADYEXIST,
                )
        else:
            return createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return BaseResponse(
                    statusCode=str(status.HTTP_503_SERVICE_UNAVAILABLE),
                    statusDescription=SYSTEMBUSY,
                )
    

def notifyUser(
        db: Session,
    title: str,
    message: str,
    userId:int,
    setting: Setting):
    logger.info("started notifying user......................")
    customer = queries.customer(db=db,userId=userId)
    if customer:
        if customer.preference:
            if customer.preference.email:
                email_body = util.templates.TemplateResponse(
                    "notification.html",
                    {"request": None, "user": customer, "message": message},
                )
                util.mailer(
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject=title,
                    toAddress=customer.email,
                )
            if customer.preference.sms:
                util.send_sms_message(
                    setting=setting,
                    toPhoneNumber=customer.phonenumber,
                    message=message,
                    transactionId=util.generateId(),
                )
            notification = NotificationModel(
                title=title,
                message=message,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            user_notification = UserNotification(customer=customer, notification=notification)
            createdNotification = queries.create(db=db, model=user_notification)
            logger.info(f"Notification sent successfully to {customer.firstname}")
        else:
            notification = NotificationModel(
                title=title,
                message=message,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            user_notification = UserNotification(customer=customer, notification=notification)
            createdNotification = queries.create(db=db, model=user_notification)
            logger.info(f"Notification sent successfully to {customer.firstname}")
    else:
        logger.info(f"User with ID {userId} not found")
        