
import logging
from utils import util
from models.model import *
from utils.constant import *
from schemas.customer import *
from sqlalchemy.orm import Session
from schemas.setting import Setting
from schemas.park import ParksResponse
from fastapi import Response,Request,status
from models.queries import productQuery

logger = logging.getLogger(__name__)


def getAllBill(db: Session):
    bills = productQuery.get_all_bill(db=db)
    logger.info(bills)
    return bills


def getSingleBill(db: Session, id: int):
    bill = productQuery.get_single_bill_by_id(db=db, id=id)
    logger.info(bill)
    return bill


def getAllBillers(db: Session):
    bills = productQuery.get_all_biller(db=db)
    logger.info(bills)
    return bills


def getSingleBiller(db: Session, id: int):
    bill = productQuery.get_single_biller_by_id(db=db, id=id)
    logger.info(bill)
    return bill

def searchMovablesRoutes(request: Request,response: Response,setting: Setting,db: Session,user: Customer,departure: str,arrival: str,searchType: str):
    try:
        logger.info(f"Started searching for {searchType} route by {user.firstname}") 
        data = []
        if departure:
            if arrival:
                if searchType == "bus":
                    data = productQuery.query_bus_routes(db=db,departure=departure,arrival=arrival,searchType=searchType)
                else:
                    data = productQuery.query_bus_routes_no_type(db=db,departure=departure,arrival=arrival)
            else:
                data = productQuery.query_bus_routes_no_type(db=db,departure=departure,arrival=arrival)
        else:
            data = productQuery.query_bus_routes_no_type(db=db,departure=departure,arrival=arrival)
        if data:
            return ParksResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
        return ParksResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=[])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ParksResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)