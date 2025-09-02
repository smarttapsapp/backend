import time 
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
from utils.dependencies import getSystemSetting, verified_user,validateTransactionPIN,validateAdmin,validateCustomer
from services import productservice,paymentservice
from utils.database import get_db
from datetime import date
from schemas.payment import *
from schemas.cashout import *
from models.model import *
from schemas.ticket import TicketResponse,TicketsResponse
from schemas.customer import Customer,CreatePINRequest
from schemas.setting import Setting
from models.model import CustomerModel

logger = logging.getLogger(__name__)

router = APIRouter()
adminRouter = APIRouter(tags=["payments"])

@router.post("/generate/qr",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def payment_via_QR(
    payload: GenerateQRRequest,
    request: Request,
    response: Response,
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
                response.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=f"PIN successfully created",
                )
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except ValidationError as e:
        logger.error(e)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(e),
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# fund wallet
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
@router.post("/threshold",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def fund_wallet_threshold(
    payload: AutoFundRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return paymentservice.saveFundThreshold(user=user,request=request,db=db,response=response,setting=setting,payload=payload,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/threshold",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def fund_wallet_threshold(
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return paymentservice.toggleFundThreshold(user=user,request=request,db=db,response=response,setting=setting,background_task=background_task)
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
@router.get("/transactions", 
    response_model=PaymentsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_payments(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: Optional[str] = Query(str(date.today())),
    endDate: Optional[str] = Query(str(date.today())),
    transaction_type: Optional[str] = Query(None),
):
    try:
        if user:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            if transaction_type and transaction_type.lower() == "all":
                return await paymentservice.payments(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                startDate=startDate,
                endDate=endDate,
                transactionType=transaction_type)
            return await paymentservice.payments(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                startDate=startDate,
                endDate=endDate,
                transactionType=transaction_type)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/transactions/{id}/{paymentType}", 
    response_model=PaymentResponse,
    response_model_exclude_unset=True,name="get single payment")
async def get_single_payment(
    id:str,
    paymentType:str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await paymentservice.getSinglePayment(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                transactionId=id,
                transactionType=paymentType
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# bus ticket payment
@router.post("/bus/buyticket",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["tickets"])
async def buy_ticket(
    payload: BuyTicketRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await paymentservice.debitBusTicket(user=user,request=request,db=db,response=response,setting=setting,payload=payload,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# train ticket payment
@router.post("/train/buyticket",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["tickets"])
async def buy_train_ticket(
    payload: BuyTrainTicketRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
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
@router.get("/tickets", 
    response_model=TicketsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_tickets(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
):
    try:
        if user:
            logger.info(startDate)
            if startDate is '' or endDate is '':
                return await paymentservice.getAllTickets(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,)
            else:
                logger.info(type(startDate))
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
                return await paymentservice.getAllTickets(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                startDate=startDate,
                endDate=endDate,
                transactionType=transaction_type)


    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# single ticket payment
@router.get("/ticket/{ticketId}/{mode}",
    response_model=TicketResponse,
    response_model_exclude_unset=True,tags=["tickets"])
async def get_ticket(
    ticketId: str,
    mode:str,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await paymentservice.singleTicket(response=response,db=db,user=user,ticketId=ticketId,mode=mode)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# nfc debit payment
@router.post("/nfc/debit",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["NFC payment"])
async def fund_wallet_nfc(
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

            return await paymentservice.nfcdebitService(payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
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
@router.get("/nfc/debit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def confirm_nfc_payment(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    transactionId: Optional[str] = Query(None),
):
    try:
        if transactionId:
            #time.sleep(5)  # Simulate a delay for processing
            return await paymentservice.getSinglePayment(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                transactionId=transactionId,
                transactionType='DEBIT'
            )
        else:
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING,)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
#  bill payment
@router.post("/bill/name-enquiry",
    response_model=BillNameEnquiryResponse,
    response_model_exclude_unset=True,tags=["Bills Payement"])
async def bill_payment_name_enquiry(
    payload: BillNameEnquiryRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await paymentservice.billerEnquiry(payload=payload,request=request,response=response,setting=setting,db=db,user=user)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillNameEnquiryResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=INVALIDACCOUNT,
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillNameEnquiryResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/bill/purchase",
    response_model=BillPaymentResponse,
    response_model_exclude_unset=True,tags=["Bills Payement"])
async def bill_payment(
    payload: BillPaymentRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await paymentservice.payBills(payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex), )
# wallet payment
@router.get("/wallet/enquiry/{accountNumber}",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["wallet"])
async def wallet_enquiry(
    accountNumber: str,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await paymentservice.walletEnquiry(
                wallet=accountNumber,
                response=response,
                db=db,
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
            statusDescription=str(ex),
        )
@router.post("/wallet/transfer",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["wallet"])
async def wallet_payment(
    payload: WalletDebitRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await paymentservice.walletTransfer(
                payload=payload,
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# redeem ticket
@router.post("/redeem/ticket",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["tickets"])
async def redeem_ticket(
    payload: RedeemRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await paymentservice.redeemTicket(user=user,db=db,request=request,response=response,setting=setting,payload=payload,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# redeem ticket
@router.get("/banks",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def getBanks(
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
):
    try:
        if user:
            return await paymentservice.getbanks(user=user,request=request,response=response,setting=setting)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/cashout/recipient",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_recipient(
    payload: AddCashoutRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await paymentservice.addCashoutRecipient(
                payload=payload,
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/cashout/request",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_request(
    payload: CashoutRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await paymentservice.addCashout(
                payload=payload,
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)


#==============================================Admin ==============================================
@adminRouter.get("/payments", 
    response_model=PaymentsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_Admin_payments(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return paymentservice.adminPayments(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@adminRouter.get("/cashouts", 
    response_model=CashoutsResponse,
    response_model_exclude_unset=True)
async def get_cashouts(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return paymentservice.listOfCashout(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
