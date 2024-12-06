
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import transactionQuery
from datetime import datetime,timedelta
from time import sleep
from schemas import otp
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import Customer
from schemas.admin import Admin
from schemas.transaction import Transaction,Transactions
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
logger = logging.getLogger(__name__)

def transactions(request: Request,response: Response,setting: Setting,db: Session,user: Customer,startDate: str,endDate: str,transactionType: str):
    try:
        logger.info(
            f"started querying transactions from {startDate} to {endDate} for {transactionType}"
        )
        sleep(5)
        if transactionType:
            return Transactions(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=transactionQuery.getAllByUser(db=db,userId=user.id,start=startDate,end=endDate,transType=transactionType)
            )
        return Transactions(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=transactionQuery.getAllByUser(db=db,userId=user.id,start=startDate,end=endDate,transType=transactionType)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Transactions(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def getAllTransactions(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Admin,
    startDate: str ,
    endDate: str ,
    transactionType: str ,
):
    try:
        logger.info(
            f"started transaction querying from {startDate} to {endDate} for {transactionType}"
        )
        if startDate and endDate and transactionType:
            startDate_object = datetime.strptime(startDate, "%Y-%m-%d").date()
            endDate_object = datetime.strptime(endDate, "%Y-%m-%d").date()
            if endDate_object >= startDate_object:
                response.status_code = status.HTTP_200_OK
                return Transactions.model_validate(
                    {
                        "statusCode": str(status.HTTP_200_OK),
                        "statusDescription": SUCCESS,
                        "data": transactionQuery.get_all(
                            db=db,
                            sql=QUERYTRANSACTIONBYDATEANDTRANSTYPE.replace(
                                "<userId>", str(user.id)
                            )
                            .replace("<start>", startDate)
                            .replace("<end>", endDate)
                            .replace("<transactionType>", transactionType),
                        ),
                    }
                )
            else:
                response.status_code = status.HTTP_200_OK
                return Transactions.model_validate(
                    {
                        "statusCode": str(status.HTTP_200_OK),
                        "statusDescription": SUCCESS,
                        "data": transactionQuery.get_all(
                            db=db,
                            sql=QUERYTRANSACTIONBYDATEANDTRANSTYPE.replace(
                                "<userId>", str(user.id)
                            )
                            .replace("<start>", startDate)
                            .replace("<end>", str(date.today()))
                            .replace("<transactionType>", transactionType),
                        ),
                    }
                )
        elif startDate and endDate and transactionType is None:
            response.status_code = status.HTTP_200_OK
            return Transactions.model_validate(
                {
                    "statusCode": str(status.HTTP_200_OK),
                    "statusDescription": SUCCESS,
                    "data": transactionQuery.get_all(
                        db=db,
                        sql=QUERYTRANSACTIONBYDATES.replace(
                            "<userId>", str(user.id)
                        )
                        .replace("<start>", startDate)
                        .replace("<end>", endDate),
                    ),
                }
            )
        else:
            response.status_code = status.HTTP_200_OK
            return Transactions.model_validate(
                {
                    "statusCode": str(status.HTTP_200_OK),
                    "statusDescription": SUCCESS,
                    "data": transactionQuery.get_all(
                        db=db,
                        sql=QUERYTRANSACTIONS.replace("<userId>", str(user.id)),
                    ),
                }
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Transactions.model_validate(
            {
                "statusCode": str(status.HTTP_400_BAD_REQUEST),
                "statusDescription": str(ex),
            }
        )
def getSingleTransactions(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Admin,
    transactionId: str ,
):
    try:
        logger.info(f"started transaction querying for {transactionId}")
        if transactionId:
            response.status_code = status.HTTP_200_OK
            return SingleTransactions.model_validate(
                {
                    "statusCode": str(status.HTTP_200_OK),
                    "statusDescription": SUCCESS,
                    "data": transactionQuery.get_one(
                        db=db,
                        sql=QUERYSINGLETRANSACTION.replace(
                            "<userId>", str(user.id)
                        ).replace("<transactionId>", transactionId),
                    ),
                }
            )
        else:
            response.status_code = status.HTTP_200_OK
            return SingleTransactions.model_validate(
                {
                    "statusCode": str(status.HTTP_200_OK),
                    "statusDescription": UNKNOWNTRANSACTION,
                }
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SingleTransactions.model_validate(
            {
                "statusCode": str(status.HTTP_400_BAD_REQUEST),
                "statusDescription": str(ex),
            }
        )
