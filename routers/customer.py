from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,Form,UploadFile,
    BackgroundTasks,
)
from schemas.customer import *
from schemas.setting import Setting
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, verified_user
from utils.database import get_db
from services import customerservice
from utils import util
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
    tags=["customer"],
)

@router.get(
    "/profile",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
)
async def get_customer_profile(
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.profile(
                request=request,
                response=responses,
                setting=Setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get(
    "/balance/{walletAccount}",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def get_customer_balance(
    walletAccount:str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.balance(
                wallet=walletAccount,
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get(
    "/analysis",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def get_customer_analytics(
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await authservice.generateAndSendOTP(
                db=db,
                userId=user.id,
                setting=Setting,
                background_task=background_task,
                response=responses
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.put("/kyc/update",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def update_customer_information(
    payload: CreatePINRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            validated_data = CreatePINRequest(**payload.model_dump())
            if updateUserPIN(
                db=db, userId=user.id, pin=get_password_hash(validated_data.pin)
            ):
                email_template = "createpin.html"
                email_body = templates.TemplateResponse(
                    email_template,
                    {"request": request, "user": user},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=Setting,
                    subject="Create PIN",
                    toAddress=user.email,
                )
                responses.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                responses.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/change/pin",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def create_transaction_PIN(
    payload: CreatePINRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            validated_data = CreatePINRequest(**payload.model_dump())
            if updateUserPIN(
                db=db, userId=user.id, pin=get_password_hash(validated_data.pin)
            ):
                email_template = "createpin.html"
                email_body = templates.TemplateResponse(
                    email_template,
                    {"request": request, "user": user},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=Setting,
                    subject="Create PIN",
                    toAddress=user.email,
                )
                responses.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                responses.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/reset/pin",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def reset_transaction_PIN(
    payload: CreatePINRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            validated_data = CreatePINRequest(**payload.model_dump())
            if updateUserPIN(
                db=db, userId=user.id, pin=get_password_hash(validated_data.pin)
            ):
                email_template = "createpin.html"
                email_body = templates.TemplateResponse(
                    email_template,
                    {"request": request, "user": user},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=Setting,
                    subject="Create PIN",
                    toAddress=user.email,
                )
                responses.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                responses.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/link/bvn",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def link_customer_bvn(
    payload: CreatePINRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            validated_data = CreatePINRequest(**payload.model_dump())
            if updateUserPIN(
                db=db, userId=user.id, pin=get_password_hash(validated_data.pin)
            ):
                email_template = "createpin.html"
                email_body = templates.TemplateResponse(
                    email_template,
                    {"request": request, "user": user},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=Setting,
                    subject="Create PIN",
                    toAddress=user.email,
                )
                responses.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                responses.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/link/nin",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def link_customer_nin(
    payload: CreatePINRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            validated_data = CreatePINRequest(**payload.model_dump())
            if updateUserPIN(
                db=db, userId=user.id, pin=get_password_hash(validated_data.pin)
            ):
                email_template = "createpin.html"
                email_body = templates.TemplateResponse(
                    email_template,
                    {"request": request, "user": user},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=Setting,
                    subject="Create PIN",
                    toAddress=user.email,
                )
                responses.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                responses.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.put("/photo/update",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def upload_customer_profile_image(
    payload: CreatePINRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            validated_data = CreatePINRequest(**payload.model_dump())
            if updateUserPIN(
                db=db, userId=user.id, pin=get_password_hash(validated_data.pin)
            ):
                email_template = "createpin.html"
                email_body = templates.TemplateResponse(
                    email_template,
                    {"request": request, "user": user},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=Setting,
                    subject="Create PIN",
                    toAddress=user.email,
                )
                responses.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                responses.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
