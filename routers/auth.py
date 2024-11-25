from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from pydantic import ValidationError
from utils.util import templates
from utils.constant import *
from typing import Annotated
from schemas.device import Device
from utils.dependencies import (
    getSystemSetting,
    validateRegistration,
)
from utils.database import get_db
from services import authservice
from models.model import AccountStatusEnum,CustomerModel
from schemas.customer import *
from schemas.setting import Setting
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])
@router.post(
    "/register",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def create_customer(
    payload: CustomerRequest,
    request: Request,
    response: Response,
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return authservice.createAccount(
            request=request,
            response=response,
            setting=setting,
            db=db,
            payload=payload,
            background_task=background_task,
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get(
    "/resend/otp",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Resend OTP for open account",
    tags=["auth"],
)
async def resendOTP(
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateRegistration)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return authservice.generateAndSendOTP(request=request,db=db,setting=setting,background_task=background_task,response=response,customer=user,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post(
    "/verify/otp",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="verify otp",
    tags=["auth"],
)
async def verifyOtp(
    payload: OTPRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateRegistration)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user.account_status == AccountStatusEnum.REG:
            return  authservice.verifyAccountOpening(
                request=request,
                response=response,
                setting=Setting,
                db=db,
                user=user,
                payload=payload,
                background_task=background_task
            )
        else:
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Already Verified",)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post("/create/pin", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def create_Transaction_PIN(
    payload: CreatePINRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateRegistration)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return authservice.create_pin(request=request,response=response,setting=setting,db=db,user=user,payload=payload,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
@router.post(
    "/forgot-password/initiate",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    tags=["auth"],
)
async def forgot_Password_Initiate(
    payload: ForgetPasswordRequest,
    request: Request,
    response: Response,
    #device: Annotated[Device, Depends(validateDevice)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return authservice.resetPasswordInitiate(
            payload=payload,
                request=request,
                response=response,
                setting=setting,
                db=db,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.put(
    "/forgot-password/final",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    tags=["auth"],
)
async def forgot_Password_Final(
    payload: ResetPasswordRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateRegistration)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    #token:  Annotated[str, Depends(util.oauth2_scheme)]
):
    try:
        return authservice.resetPasswordFinal(
            request=request,
                db=db,
                response=response,
                user=user,
                setting=setting,
                payload=payload,
                background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/login",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    tags=["auth"],
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return authservice.login(
            request=request,
            db=db,
            response=response,
            setting=setting,
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

