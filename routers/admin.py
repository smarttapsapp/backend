from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.response import *
from schemas.request import *
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import (
    getSystemSetting,validateAdmin,
)
from utils.database import get_db
from services import adminservice
from schemas.admin import *
from schemas.setting import Setting
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")

# admin
@router.post(
    "/login",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return adminservice.authenticate_user(
            db=db,
            response=response,
            setting=setting,
            request=request,
            payload=payload,
            background_task=background_task,
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/users",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Open account on Better",
)
async def createAdmin(
    request: Request,
    payload: AdminCreate,
    responses: Response,
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        userRequest = AdminCreate.model_validate(payload)
        logger.info(userRequest.model_dump_json())
        return adminservice.createAccount(request=request,response=responses,setting=Setting,db=db,payload=payload,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get("/users", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get all user cashpoints transactions")
async def getAdmins(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return adminservice.getAdminUsers(
                db=db,
                setting=Setting,
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
#dashboard 
@router.get("/dashboard", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get dashboard Analytics")
async def getDashboardRequest(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return adminservice.getDashboardAnalytics(
                db=db,
                setting=Setting,
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
#dashboard 
@router.get("/dashboard_product", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get dashboard Analytics")
async def getDashboardProductRequest(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return adminservice.getDashboardByProducts(
                db=db,
                setting=Setting,
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








