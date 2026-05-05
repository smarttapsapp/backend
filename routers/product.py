
import logging
from utils.constant import *
from typing import Annotated
from fastapi import APIRouter
from fastapi import (
    Depends,
    Query,
    status,
    Response,
    Request,BackgroundTasks
)
from schemas.admin import Admin
import time
from utils.database import get_db
from sqlalchemy.orm import Session
from schemas.bus_schedule import BusSchedulesMobileResponse
from schemas.route import RoutesResponse,RouteResponse,TrainRoutesResponse,TrainRouteResponse
from services import productservice,bus
from schemas.customer import Customer
from schemas.setting import Setting
from schemas.product import ProductsResponse
from schemas.station import StationsMobileResponse
from schemas.bus import BusesResponse
from schemas.admin import ProvidersResponse
from schemas.bus_route import BusRoutesResponse,BusRouteResponse
from schemas.beneficiary import *
from models.model import CustomerModel,AdminModel
from utils.dependencies import getSystemSetting, verified_user,validateTransactionPIN,validateAdmin

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["products"],
)
adminRouter = APIRouter(tags=["products"])
@router.get("/bills",
    response_model=ProductsResponse,
    response_model_exclude_unset=True,)
async def get_All_Billers(
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    settings: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            bill = productservice.getAllBill(db=db)
            logger.info(bill)
            if bill:
                return ProductsResponse.model_validate(
                    {
                        "statusCode": str(status.HTTP_200_OK),
                        "statusDescription": SUCCESS,
                        "data": bill,
                    }
                )

        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return ProductsResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=UNKNOWNUSER,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ProductsResponse(
            statusCode=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            statusDescription=str(ex),
        )
@router.get("/routes/{mode}",
    response_model=RoutesResponse,
    response_model_exclude_unset=True,)
async def get_available_routes(
    mode:str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        if user:
            return productservice.availableRoutes(mode=mode,request=request,response=response,setting=setting,db=db,user=user)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,data=[])
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,data=[])
@router.get("/bus_search",
    response_model=BusSchedulesMobileResponse,
    response_model_exclude_unset=True,tags=['bus'])
async def get_Bus_Routes(
    response: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    db: Annotated[Session, Depends(get_db)],
    departure: str = Query(None),
    arrival: str = Query(None),
    latitude: str = Query(None),
    longitude: str = Query(None),
):
    try:
        logger.info(type(arrival))
        if user:
            if departure and arrival:
                return await bus.searchMovablesRoutes(response=response,db=db,latitude=latitude,longitude=longitude,departure=departure,arrival=arrival)
            elif departure and not arrival:
                return await bus.searchMovablesRoutes(response=response,db=db,latitude=latitude,longitude=longitude,departure=departure)
            elif arrival and not departure:
                return await bus.searchMovablesRoutes(response=response,db=db,latitude=latitude,longitude=longitude,arrival=arrival)
            else:
                return await bus.searchMovablesRoutes(response=response,db=db,latitude=latitude,longitude=longitude)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BusSchedulesMobileResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusSchedulesMobileResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/trip/seat/{tripId}",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=['bus'])
async def get_Bus_Seats(
    tripId:int,
    response: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            r = await bus.get_trip_seats(response=response,db=db,tripId=tripId)
            logger.info(r)
            return r
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/bus_provider/{providerId}",
    response_model=BusRoutesResponse,
    response_model_exclude_unset=True,tags=['bus'])
async def get_Bus_ProviderRoutes(
    providerId: int,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await productservice.getBusproviderRoutes(response=response,adminId=providerId,db=db)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BusRoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusRoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/bus_provider",
    response_model=ProvidersResponse,
    response_model_exclude_unset=True,tags=['bus'])
async def get_Bus_Providers(
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await productservice.getBusprovider(response=response,setting=setting,db=db,user=user)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ProvidersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProvidersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/stations/{mode}",
    response_model=StationsMobileResponse,
    response_model_exclude_unset=True,)
async def get_Stations(
    mode:str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        if user:
            if mode == "train":
                return productservice.stations(mode=mode,request=request,response=response,setting=setting,db=db,user=user)
            return bus.stations(response=response,db=db)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return StationsMobileResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,data=[])
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsMobileResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,data=[])
@router.get("/train_search",
    response_model=TrainRoutesResponse,
    response_model_exclude_unset=True,tags=['train'])
async def get_Trains_Routes(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    departure: str = Query(None),
    arrival: str = Query(None),
    searchType: str = Query("train"),
    latitude: str = Query(None),
    longitude: str = Query(None),
):
    try:
        if user:
            return productservice.searchTrainRoutes(response=response,db=db,user=user,departure=departure,arrival=arrival,mode=searchType,latitude=latitude,longitude=longitude)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return TrainRoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TrainRoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/train_provider/{providerId}",
    response_model=RoutesResponse,
    response_model_exclude_unset=True,tags=['train'])
async def get_Train_ProviderRoutes(
    providerId: int,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await productservice.getTrainproviderRoutes(response=response,adminId=providerId,db=db)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/train_provider",
    response_model=ProvidersResponse,
    response_model_exclude_unset=True,tags=['train'])
async def get_Bus_Providers(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await productservice.getTrainprovider(response=response,setting=setting,db=db,user=user)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ProvidersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProvidersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/schedule/{mode}/{routeId}",
    response_model=RouteResponse,
    response_model_exclude_unset=True,)
async def get_Trains_Routes(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    mode: str,
    routeId: str 
):
    try:
        if user:
            time.sleep(5)
            return productservice.searchTrainByRoute(routeId=routeId,mode=mode,request=request,response=response,setting=setting,db=db,user=user)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return RouteResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RouteResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/beneficiaries/{billerType}",
    response_model=BeneficiariesResponse,
    response_model_exclude_unset=True,)
async def get_beneficiaries_by_product(
    billerType:str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    settings: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return productservice.getBeneficiaries(db=db,response=response,transType=billerType,user=user)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BeneficiariesResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=UNKNOWNUSER,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BeneficiariesResponse(
            statusCode=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            statusDescription=str(ex),
        )
@router.post("/add-beneficiary",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def add_beneficiary(
    payload: AddBeneficiaryRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return productservice.addBeneficiary(db=db,request=request,response=response,payload=payload,user=user)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex), )
@router.delete("/delete-beneficiary/{beneficiaryId}",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def delete_beneficiary(
    beneficiaryId: str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return productservice.deleteBeneficiary(db=db,beneficiaryId=beneficiaryId,user=user)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex), )
#==============================================Admin ==============================================
