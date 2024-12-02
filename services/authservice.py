
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import authQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)

def createAccount(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        payload: CustomerRequest,
        background_task: BackgroundTasks,):
    try:
        user = authQuery.userByEmailOrPhone(db=db,email=payload.email,phonenumber=payload.phonenumber)
        if user and user.account_status != AccountStatusEnum.REG:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST,)
        elif user and user.account_status == AccountStatusEnum.REG:
            return createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response,customer=user)
        else:
            return createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def createUserAccount(db: Session,setting: Setting,payload: CustomerRequest, background_task: BackgroundTasks, request: Request,response: Response,customer:CustomerModel=None):
    if customer:
        logger.info(f"Started resending verification for user {payload.email} {customer.account_status}")
        latestOtp = authQuery.get_latest_otp(db=db,userId=customer.id)
        if latestOtp:
            if latestOtp.expired_at > datetime.now():
                authToken = util.create_access_token(setting=setting,credentials={"username": customer.email,"password": latestOtp.otp},exp=60)
                if authToken:
                    email_body = util.templates.TemplateResponse("otp.html",{"request": request, "user": customer,"otp":latestOtp},)
                    background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject=f"Verification",
                    toAddress=customer.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=f"Please enter the OTP sent to {util.mask_email(customer.email)} to complete your registration",data={"token":authToken[0],"expires":authToken[1]})
            return generateAndSendOTP(request=request,db=db,response=response,setting=setting,customer=customer,background_task=background_task)
        else:
            return generateAndSendOTP(request=request,db=db,response=response,setting=setting,customer=customer,background_task=background_task)
    else:
        user = CustomerModel(
            firstname=payload.firstname,
            lastname=payload.lastname,
            email=payload.email,
            phonenumber=payload.phonenumber,
            username=payload.username,
            password=util.get_password_hash(password=payload.password),
            )
        createdAccount = authQuery.create_account(db=db, user=user)
        if createdAccount:
            return generateAndSendOTP(request=request,db=db,setting=setting,background_task=background_task,response=response,customer=createdAccount)
def generateAndSendOTP(request: Request,db: Session,setting: Setting,background_task:BackgroundTasks,response: Response,customer:CustomerModel):
    newOtp = authQuery.create_otp(db=db,otp=OTPModel(otp=util.generateOTP(), servicename="openAccount", user_id=customer.id,
                created_at=datetime.now(),expired_at=(datetime.now() + timedelta(minutes=15)),updated_at=datetime.now(),))
    if newOtp:
        authToken = util.create_access_token(setting=setting,credentials={"username": customer.email,"password": newOtp.otp},exp=60)
        if authToken:
            email_body = util.templates.TemplateResponse("otp.html",{"request": request, "user": customer,"otp":newOtp},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=f"Verification",toAddress=customer.email,)
        return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=f"Please enter the OTP sent to {util.mask_email(customer.email)} to complete your registration",data={"token":authToken[0],"expires":authToken[1] })
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to send otp at the moment",)
def verifyAccountOpening(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: CustomerModel,
    payload: OTPRequest,
    background_task: BackgroundTasks,):
    try:
        logger.info(user.otps)
        latest = authQuery.get_otp_by_code(db=db,code=payload.otp,userId=user.id)
        if latest:
            logger.info(latest)
            current_datetime = datetime.now()
            if latest.expired_at >= current_datetime:
                wallet = AccountModel(user_id=user.id,walletAccount=util.formatPhoneShort(user.phonenumber),availableBalance="0",referenceNo=util.formatPhoneShort(user.phonenumber),accountStatus=AccountStatusEnum.ACTIVE.value,created_at = datetime.now(),updated_at = datetime.now())
                user.updated_at = current_datetime
                user.account_status = AccountStatusEnum.ACTIVE
                user.email_verified = True
                user.wallet = wallet
                user.date_of_birth = str(datetime.now().date())
                verifiedUser = authQuery.create_account(db=db,user=user)
                if verifiedUser:
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
                else:
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Please try again",)
            else:
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="User OTP failed or expired",)

        #latestOTP:otp.OTP = sorted(user.otps, key=lambda p: p.id, reverse=True)[0]
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def create_pin(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: CustomerModel,
    payload: CreatePINRequest,
    background_task: BackgroundTasks,):
    try:
        if user.pin:
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="PIN already exist",)
        if payload.pin == payload.confirmPin:
            user.pin = util.get_password_hash(password=payload.pin)
            user.updated_at = datetime.now()
            updatedUser = authQuery.create_account(db=db,user=user)
            if updatedUser:
                email_body = util.templates.TemplateResponse("createpin.html",{"request": request, "user": user},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Create PIN",toAddress=user.email,)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=f"PIN successfully created",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Create PIN Failed",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="PIN Mismatched",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def resetPasswordInitiate(
    payload: ForgetPasswordRequest,
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    background_task: BackgroundTasks,
):
    try:
        user = authQuery.userByEmailOrPhone(db=db,email=payload.email,phonenumber=payload.email)
        if user:
            logger.info(f"started resetPasswordInitiate")
            dbOtp = OTPModel(
                otp=util.generateOTP(),
                user_id=user.id,
                status=OTPStatusEnum.OPEN,
                servicename="resetPasswordInitiate",
                created_at=datetime.now(),
                expired_at=datetime.now()+timedelta(minutes=5),
                updated_at=datetime.now(),
            )
            createdOTP = authQuery.create_otp(db=db, otp=dbOtp)
            if createdOTP:
                authToken = util.create_access_token(setting=setting,credentials={"username": user.email,"password": createdOTP.otp},exp=10)
                if authToken:
                    email_body = util.templates.TemplateResponse("otp.html",{"request": request, "user": user,"otp":createdOTP},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=f"Password Reset",toAddress=user.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"token":authToken[0],"expires":authToken[1] })
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Reset Password Fail",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Reset Password Fail",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Email or Phone number",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def resetPasswordFinal(request:Request,db:Session,response:Response,user:CustomerModel,setting: Setting,payload:ResetPasswordRequest, background_task: BackgroundTasks):
    try:
        otp = authQuery.otpViaCodeAndServicename(db=db,code=payload.otp,servicename="resetPasswordInitiate",userId=user.id)
        if otp and otp.expired_at > datetime.now():
            if payload.password == payload.confirmPassword:
                user.password = util.get_password_hash(payload.password)
                user.updated_at = datetime.now()
                otp.status = OTPStatusEnum.CLOSED
                otp.updated_at = datetime.now()
                updatedUser = authQuery.create_account(db=db,user=user)
                if updatedUser:
                    updatedOtp = authQuery.create_otp(db=db,otp=otp)
                    if updatedOtp:
                        response.status_code = status.HTTP_200_OK
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Password Reset Successful",)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to complete Password Reset",)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to complete Password Reset",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Error! Password mismatch",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid/expired OTP",)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def login(request:Request,db: Session,response: Response,setting: Setting, payload: LoginRequest,background_task: BackgroundTasks,):
    user = authQuery.userByEmailOrPhone( db=db,email=payload.username,phonenumber=util.formatPhoneWithDialingCode(payload.username))
    if user:
        if util.verify_password(payload.password, user.password) is True:
            if user.account_status == AccountStatusEnum.ACTIVE:
                authToken = util.create_access_token(setting=setting,credentials={"username": user.email,"password": payload.password,},exp=600)
                logger.info(authToken)
                return BaseResponse(statusCode= str(status.HTTP_200_OK),statusDescription= SUCCESS,data={"token":authToken[0],"expires":authToken[1]})
            else:
                response.status_code= status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=f"Your account is {user.account_status}")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
