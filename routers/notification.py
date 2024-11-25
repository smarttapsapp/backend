from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.response import BaseResponse
from schemas.request import *
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting,validateAdmin,verified_user
from utils import util
from utils.database import get_db
from services import notificationservice
from schemas.admin import Admin
from schemas.customer import Customer
from schemas.setting import Setting
import logging
from schemas.notification import NotificationRequest,NotificationsResponse,NotificationResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notification"])
adminRouter = APIRouter(tags=["notification"])

# notification
@router.get("", 
    response_model=NotificationsResponse,
    response_model_exclude_unset=True,name="get customer notifications")
async def getNotificationsRequest(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.getNotifications(
                db=db,
                userId=user.id,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return NotificationsResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get("/{id}", 
    response_model=NotificationResponse,
    response_model_exclude_unset=True,name="get single notification")
async def getNotificationRequest(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.getNotification(
                id=id,
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.patch("/{id}", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="read notification")
async def readNotificationRequest(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.readNotification(
                id=id,
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/{id}", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get dashboard Analytics")
async def deleteNotificationRequest(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.deleteNotification(
                id=id,
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )

# Admin notifictions
@adminRouter.get("/notifications", 
    response_model=NotificationsResponse,
    response_model_exclude_unset=True,name="get notifications")
async def getNotificationsRequest(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.getNotifications(
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return NotificationsResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@adminRouter.post("/notification", 
    response_model=BaseResponse,
    response_model_exclude_unset=True)
async def add_Notification(
    payload:NotificationRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.postNotification(
                payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@adminRouter.get("/notification/{id}", 
    response_model=NotificationResponse,
    response_model_exclude_unset=True)
async def get_Notification(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.getNotification(
                id=id,
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@adminRouter.delete("/notification/{id}", 
    response_model=BaseResponse,
    response_model_exclude_unset=True)
async def delete_Notification(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return notificationservice.deleteNotification(
                id=id,
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
