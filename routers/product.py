from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
)
from schemas.product import ProductsResponse
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
async def getAllBillers(
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
