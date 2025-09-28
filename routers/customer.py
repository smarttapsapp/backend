from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Query,
    Response,
    Request,Form,UploadFile,
    BackgroundTasks,File
)
from schemas.customer import *
from schemas.support_ticket import *
from schemas.support_comment import SupportTicketCommentRequest
from schemas.setting import Setting
from models.model import CustomerModel
from models.model import AdminModel
from sqlalchemy.orm import Session
from utils.constant import *
from datetime import date
from typing import Annotated
from utils.dependencies import getSystemSetting, verified_user,validateTransactionPIN,validateAdmin,validateCustomer
from utils.database import get_db
from services import customerservice
from utils import util
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
adminRouter = APIRouter(tags=["customer"])

@router.get(
    "/profile",
    response_model=CustomerResponse,
    response_model_exclude_unset=True, tags=["customer"]
)
async def get_customer_profile(
    request: Request,
    responses: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
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
    response_model_exclude_unset=True, tags=["customer"]
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
@router.post("/change/pin",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["customer"])
async def change_transaction_pin(
    payload: ChangePINRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateTransactionPIN)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await customerservice.changepin(
                request=request,
                user=user,
                response=response,
                setting=Setting,
                db=db,
                payload=payload,
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
@router.post("/change/password",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["customer"])
async def change_transaction_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await customerservice.changepassword(
                request=request,
                user=user,
                response=response,
                setting=Setting,
                db=db,
                payload=payload,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/reset/pin",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["customer"])
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
            statusDescription=SYSTEMBUSY,
        )
@router.post("/link",
    response_model=BaseResponse,
    response_model_exclude_unset=True,  name="to update user information", tags=["customer"])
async def updateCustomerInformation(
    payload:VerificationRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    settings: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await customerservice.performAction(request=request,payload=payload,user=user,response=response,setting=settings,db=db,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post("/update/otp",
    response_model=BaseResponse,
    response_model_exclude_unset=True,  name="verify user account information by OTP", tags=["customer"])
async def updateAccountInfoVerification(
    payload: InfoVerificationRequest,
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    settings: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await customerservice.handleOTPVerification(
                request=request,
                user=user,
                response=response,
                setting=settings,
                db=db,
                payload=payload,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post("/update/kin",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def update_customer_information(
    payload: NextOfKinRequest,
    request: Request,
    responses: Response,
    user: Annotated[CustomerModel, Depends(verified_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await customerservice.updateNextOfKin(
                payload=payload,
                request=request,
                user=user,
                response=responses,
                setting=setting,
                db=db,
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
@router.post("/photo/update",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def upload_customer_profile_image(
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    img: UploadFile = File(...),
):
    try:
        return await customerservice.uploadProfileImage(response=response,db=db,user=user,setting=Setting,request=request,background_task=background_task,img=img)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get("/tickets", 
    response_model=SupportTicketsResponse,
    response_model_exclude_unset=True,tags=['customer'])
async def get_customer_support_tickets(
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        return await customerservice.listOfSupportTickets(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SupportTicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/ticket/open",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def open_support_ticket(
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    attachment: UploadFile = File(...),
    subject: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
):
    try:
        payload = SupportTicketRequest(subject=subject,description=description,priority=priority,status=OTPStatusEnum.OPEN)
        return await customerservice.openSupportTicket(response=response,db=db,user=user,setting=Setting,request=request,background_task=background_task,payload=payload,attachment=attachment)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post("/ticket/comment",
    response_model=BaseResponse,
    response_model_exclude_unset=True,)
async def support_ticket_comment(
    request: Request,
    response: Response,
    user: Annotated[CustomerModel, Depends(validateCustomer)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    attachment: UploadFile = File(...),
    ticketId: str = Form(...),
    comment: str = Form(...),
):
    try:
        payload = SupportTicketCommentRequest(
            comment=comment,ticket_id=ticketId,created_at=datetime.now(),updated_at=datetime.now()
        )
        return await customerservice.addSupportTicketComment(response=response,db=db,user=user,setting=Setting,request=request,background_task=background_task,payload=payload,attachment=attachment)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
#==============================================Admin ==============================================
@adminRouter.get("/customers", 
    response_model=CustomersResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_Admin_customers(
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
                    return CustomersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return customerservice.listOfCustomer(
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
        return CustomersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
