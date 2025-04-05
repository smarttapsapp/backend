
import logging
import schemas.station
from utils import util
from models.model import *
from utils.constant import *
from schemas.customer import *
from sqlalchemy.orm import Session
from schemas.setting import Setting
from schemas.park import ParksResponse
from schemas.station import StationsResponse
from schemas.route import RoutesResponse
from fastapi import Response,Request,status
from models.queries import productQuery,queries
from schemas.beneficiary import *

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
def searchTrainRoutes(request: Request,response: Response,setting: Setting,db: Session,user: Customer,departure: str,arrival: str,seatType: str,operationTime:str):
    try:
        logger.info(f"Started searching for train from {departure} to {arrival} with {seatType} for {operationTime}") 
        data = []
        data = productQuery.query_train_routes(db=db,departure=departure,arrival=arrival,seatType=seatType,takeOffTime=operationTime)
        return RoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
        return ParksResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=[])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def stations(mode:str,request: Request,response: Response,setting: Setting,db: Session,user: Customer):
    try:
        logger.info(f"Started getting stations")
        if mode.lower() == "bus":
            data = queries.query_stations(db=db,mode=mode)
        elif mode == "train":
            data = queries.query_stations(db=db,mode=mode)
        else:
            data = queries.query_stations(db=db,mode=mode)
        if not data:
            data = queries.query_stations(db=db,mode=mode)
        data = []
        data = queries.query_stations(db=db,mode=mode)
        if data:
            return StationsResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
        return StationsResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def getBeneficiaries(db: Session,response: Response,transType:str,user:Customer):
    beneficiaries = productQuery.queryBeneficiaryByTransactionType(db=db,transactionType=transType,userId=user.id)
    if beneficiaries:
        return BeneficiariesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=beneficiaries)
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BeneficiariesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
def addBeneficiary(db: Session,request:Request,response:Response,payload:AddBeneficiaryRequest,user:CustomerModel):
    existedBeneficiary = productQuery.querySinglebeneficiary(db=db,transactionType=payload.transaction_type,userId=user.id,customerId=payload.customerId)
    if existedBeneficiary:
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST)
    biller = productQuery.get_single_biller_by_billerId(db=db,billerId=payload.billercode)
    if biller:
        newBeneficiary = BeneficiaryModel(
        transaction_type = payload.transaction_type,
        nickname = payload.nickname,
        customerId = payload.customerId,
        billercode = biller.billerId,
        billername =biller.billerName,
        logo = biller.logo,
        user_id = user.id)
        created = productQuery.create(db=db,model=newBeneficiary)
        if created:
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
def deleteBeneficiary(db: Session,beneficiaryId:str,user:Customer):
    deleted = productQuery.deleteRecord(db=db,id=beneficiaryId,userId=user.id)
    if deleted:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)