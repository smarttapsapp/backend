from fastapi import APIRouter
from fastapi import (
    Depends,
    Query,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from typing import Annotated
from utils import util
from utils.constant import *
from datetime import date
from utils.dependencies import getSystemSetting, validateAdmin,verified_user
from utils.database import get_db
from schemas.admin import Admin
from schemas.customer import Customer
from services import transactionservice
import logging
from schemas.setting import Setting
from schemas.transaction import Transactions,BaseResponse

logger = logging.getLogger(__name__)


router = APIRouter(tags=["transactions"])
adminRouter = APIRouter(tags=["transactions"])

# transaction
@router.get("", 
    response_model=Transactions,
    response_model_exclude_unset=True,name="get customer transactions")
async def get_transactions(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(str(date.today())),
    endDate: str = Query(str(date.today())),
    transaction_type: str = Query(None),
):
    try:
        return transactionservice.transactions(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                startDate=startDate,
                endDate=endDate,
                transactionType=transaction_type
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Transactions(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get("/{id}", 
    response_model=Transactions,
    response_model_exclude_unset=True,name="get single transaction")
async def get_transaction(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return transactionservice.getNotification(
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
# transaction
@adminRouter.get("", 
    response_model=Transactions,
    response_model_exclude_unset=True,name="get customer transactions")
async def get_transactions(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(str(date.today())),
    endDate: str = Query(str(date.today())),
    transaction_type: str = Query(None),
):
    try:
        if user:
            return transactionservice.getNotifications(
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Transactions(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@adminRouter.get("/{id}", 
    response_model=Transactions,
    response_model_exclude_unset=True,name="get single transaction")
async def get_transaction(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return transactionservice.getNotification(
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
