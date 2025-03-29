import logging
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
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, verified_user,validateTransactionPIN
from services import productservice,paymentservice
from utils.database import get_db
from datetime import date
from schemas.payment import *
from schemas.customer import Customer,CreatePINRequest
from schemas.setting import Setting

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])

@router.post("/enquiry",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def wallet_enquiry(
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
            responses.status_code = status.HTTP_200_OK
            return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
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
            statusDescription=str(ex),
        )
@router.post("/transfer",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def wallet_payment(
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
            responses.status_code = status.HTTP_200_OK
            return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
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
            statusDescription=str(ex),
        )
@router.post("/generate/qr",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def payment_via_QR(
    payload: GenerateQRRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(validateTransactionPIN)],
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
@router.post("/via/nfc",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def payment_via_NFC(
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
            responses.status_code = status.HTTP_200_OK
            return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
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
            statusDescription=str(ex),
        )
@router.post("/bills",
    response_model=BaseResponse,
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
            bill = paymentService.getAllBill(db=db)
            logger.info(bill)
            if bill:
                return BillResponse.model_validate(
                    {
                        "statusCode": str(status.HTTP_200_OK),
                        "statusDescription": SUCCESS,
                        "data": bill,
                    }
                )

        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BillResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=UNKNOWNUSER,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BillResponse(
            statusCode=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            statusDescription=str(ex),
        )

@router.post("/fund",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def fund_wallet(
    payload: FundRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return paymentservice.fundViaPaystack(user=user,request=request,db=db,response=response,setting=setting,amount=payload.amount)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/notification",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def fund_notifications(
    request: Request,
    response: Response,
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await paymentservice.fundNotificationViaPaystack(request=request,db=db,response=response,setting=setting,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# payments
@router.get("s", 
    response_model=PaymentsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_payments(
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
        return paymentservice.payments(
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
        return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/{id}", 
    response_model=PaymentResponse,
    response_model_exclude_unset=True,name="get single payment")
async def get_payment(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return paymentservice.payment(
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
        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/buyticket",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def buy_ticket(
    payload: FundRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return paymentservice.fundViaPaystack(user=user,request=request,db=db,response=response,setting=setting,amount=payload.amount)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/buytrainticket",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def buy_train_ticket(
    payload: BuyTrainTicketRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return paymentservice.fundViaPaystack(user=user,request=request,db=db,response=response,setting=setting,amount=payload.amount)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/debit",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def fund_wallet(
    payload: DebitRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return paymentservice.debitService(payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
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
            statusDescription=str(ex),
        )
