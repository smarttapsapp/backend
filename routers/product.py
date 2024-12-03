from fastapi import APIRouter
from fastapi import (
    Depends,
    Query,
    status,
    Response,
    Request,
)
from schemas.product import ProductsResponse
from schemas.park import ParksResponse
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, verified_user
from services import productservice
from schemas.customer import Customer
from schemas.setting import Setting
from utils.database import get_db
from schemas.admin import Admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["products"],
)
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
@router.get("/bus_search",
    response_model=ParksResponse,
    response_model_exclude_unset=True,)
async def get_Bus_Routes(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    departure: str = Query(None),
    arrival: str = Query(None),
    searchType: str = Query("bus"),
):
    try:
        if user:
            return productservice.searchMovablesRoutes(request=request,response=response,setting=setting,db=db,user=user,departure=departure,arrival=arrival,searchType=searchType)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ParksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ParksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
