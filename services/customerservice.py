
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import queries
from datetime import datetime,timedelta
from schemas import otp
from services.notificationservice import notifyUser
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.admin import Admin
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)

def profile(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: Customer,
        background_task: BackgroundTasks,):
    try:
        return CustomerResponse(
                    statusCode=str(status.HTTP_200_OK),
                    statusDescription=SUCCESS,
                    data=Customer.model_validate(user)
                )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomerResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
def balance(
        wallet:str,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: Customer,
        background_task: BackgroundTasks,):
    try:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=user.wallet.availableBalance)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
def performAction(request:Request,payload:VerificationRequest,user: Customer,response: Response,setting: Setting,db: Session,background_task:BackgroundTasks):
    if payload.action.upper() == "NIN":
        return ninverification(
                        request=request,
                    user=user,
                    response=response,
                    setting=setting,
                    db=db,
                    nin=payload.nin,
                    background_task=background_task
                )
    elif payload.action.upper() == "BVN":
        return bvnverification(
                        request=request,
                    user=user,
                    response=response,
                    setting=setting,
                    db=db,
                    bvn=payload.nin,
                    background_task=background_task
                )
    elif payload.action.upper() == "EMAIL":
        return submitEmailForVerification(
                        request=request,
                    user=user,
                    response=response,
                    setting=setting,
                    db=db,
                    email=payload.nin,
                    background_task=background_task
                )
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNABLE,)
def submitEmailForVerification(
    request: Request,
    user: Customer,
    response: Response,
    setting: Setting,
    db: Session,
    email: str,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started updating/verification of account with email for {user.firstname} with {email}"
        )
        user.email = email
        userRecord = queries.update_user_agent_records(
            db=db, id=user.id, user=user
        )
        if userRecord:
            otpModel = OTPModel(
                otp=util.generateOTP(),
                servicename="emailVerification",
                user_id=user.id,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=15))
                )
            createdOtp = queries.create(db=db,model=otpModel)
            if createdOtp:
                email_body = util.templates.TemplateResponse(
                        "otp.html",
                        {"request": request, "user": userRecord,"otp":createdOtp.otp},
                    )
                background_task.add_task(
                        util.mailer,
                        str(email_body.body, "utf-8"),
                        setting=setting,
                        subject="Email OTP Verification",
                        toAddress=userRecord.email,
                    )
                response.status_code = status.HTTP_200_OK
                return BaseResponse(
                    statusCode =str(status.HTTP_200_OK),
                   statusDescription = SUCCESS, )
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                   statusDescription = SYSTEMBUSY,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                   statusDescription = SYSTEMBUSY, )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
                statusCode =str(status.HTTP_400_BAD_REQUEST),
               statusDescription = str(ex), )
def bvnverification(
    request: Request,
    user: Customer,
    response: Response,
    setting: Setting,
    db: Session,
    bvn: str,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started updating/verification of account with bvn for {user.firstname} with {bvn}"
        )
        userRecord = queries.updateUserBvn(
            db=db, userId=user.id, bvn=bvn
        )
        if userRecord:
            otpModel = OTPModel(
                otp=util.generateOTP(),
                servicename="bvnVerification",
                user_id=user.id,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=15)))
            createdOtp = queries.create(db=db,model=otpModel)
            if createdOtp:
                email_body = util.templates.TemplateResponse(
                        "otp.html",
                        {"request": request, "user": userRecord,"otp":createdOtp.otp},
                    )
                background_task.add_task(
                        util.mailer,
                        str(email_body.body, "utf-8"),
                        setting=setting,
                        subject="BVN OTP Verification",
                        toAddress=user.email,
                    )
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                   statusDescription = SYSTEMBUSY,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                   statusDescription = SYSTEMBUSY,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),
               statusDescription = str(ex), )
def ninverification(
    request: Request,
    user: Customer,
    response: Response,
    setting: Setting,
    db: Session,
    nin: str,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started updating/verification of account with bvn for {user.firstname} with {nin}"
        )
        userRecord = queries.updateUserNiN(
            db=db, userId=user.id, nin=nin
        )
        if userRecord:
            otpModel = OTPModel(
                otp=util.generateOTP(),
                servicename="ninVerification",
                user_id=user.id,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=15)))
            createdOtp = queries.create(db=db,model=otpModel)
            if createdOtp:
                email_body = util.templates.TemplateResponse(
                        "otp.html",
                        {"request": request, "user": userRecord,"otp":createdOtp.otp},
                    )
                background_task.add_task(
                        util.mailer,
                        str(email_body.body, "utf-8"),
                        setting=setting,
                        subject="BVN OTP Verification",
                        toAddress=user.email,
                    )
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                   statusDescription = SYSTEMBUSY,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                   statusDescription = SYSTEMBUSY )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),
               statusDescription = str(ex),)
def handleOTPVerification(
    request: Request,
    user: Customer,
    response: Response,
    setting: Setting,
    db: Session,
    payload: InfoVerificationRequest,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started verification of account with nin for {user.firstname} with {payload.action}"
        )
        if payload.action:
            otpQuery = ""
            if payload.action.lower() == "nin":
                user.nin_verified = True
                otpQuery = "ninVerification"
            if payload.action.lower() == "bvn":
                user.bvn_verified = True
                otpQuery = "bvnVerification"
            if payload.action.lower == "email":
                user.email_verified = True
                otpQuery = "emailVerification"
            latestOtp = queries.get_latest_otp_by_servicename(userId=user.id,servicename=otpQuery,db=db)
            if latestOtp:
                current_datetime = datetime.now()
                if latestOtp.expired_at >= current_datetime:
                    if latestOtp.otp == payload.otp:
                        userRecord = queries.update_user_agent_records(db=db, id=user.id, user=user)
                        if userRecord:
                            latestOtp.status = OTPStatusEnum.CLOSED
                            latestOtp.updated_at = current_datetime
                            createdOtp = queries.create(db=db,model=latestOtp)
                            if createdOtp:
                                background_task.add_task(notifyUser,db=db,title=f"{payload.action.capitalize()} Verification", message=f"Your {payload.action.capitalize()} Verification Successful",userId=user.id, setting=setting)
                                email_body = util.templates.TemplateResponse(
                                        "success.html",{"request": request, "user": userRecord,"message":f"Your {payload.action.capitalize()} Verification Successful"},
                                    )
                                background_task.add_task(
                                        util.mailer,
                                        str(email_body.body, "utf-8"),
                                        setting=setting,
                                        subject=f"{payload.action.capitalize()} Verification Successful",
                                        toAddress=userRecord.email,
                                    )
                                response.status_code = status.HTTP_200_OK
                                return BaseResponse(
                                    statusCode =str(status.HTTP_200_OK),
                                   statusDescription = SUCCESS,
    
                                )
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(

                                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                                   statusDescription = SYSTEMBUSY,

                            )
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(

                                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                                   statusDescription = SYSTEMBUSY,

                            )
                    else:
                        logger.info(latestOtp.otp)
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(

                                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                                   statusDescription ="OTP is invalid/expired",

                            )
                else:
                    logger.info(latestOtp.expired_at)
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(
                        statusCode =str(status.HTTP_400_BAD_REQUEST),
                                   statusDescription ="OTP is invalid/expired",

                            )
            else:
                logger.info(latestOtp.status)
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),
                                   statusDescription ="OTP is invalid/expired",
                            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(

                                    statusCode =str(status.HTTP_400_BAD_REQUEST),
                                   statusDescription ="Invalid Request",

                            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
                statusCode =str(status.HTTP_400_BAD_REQUEST),
               statusDescription = str(ex),)
def changepin(
    request: Request,
    user: CustomerModel,
    response: Response,
    setting: Setting,
    db: Session,
    payload: ChangePINRequest,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started chnage pin for {user.firstname}"
        )
        if payload.newPin and payload.confirmPin:
            if payload.newPin == payload.confirmPin:
                user.pin = util.get_password_hash(payload.newPin)
                userRecord = queries.create(db=db,model=user)
                if userRecord:
                    background_task.add_task(notifyUser,db=db,title=f"Change PIN", message=f"PIN change Successful",userId=user.id, setting=setting)
                    email_body = util.templates.TemplateResponse("success.html",{"request": request, "user": userRecord,"message":f"PIN change Successful"},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=f"Change PIN",toAddress=userRecord.email,)
                    response.status_code = status.HTTP_200_OK
                    return BaseResponse(
                        statusCode =str(status.HTTP_200_OK),
                       statusDescription = SUCCESS,
                    )
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = FAILED,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = "PIN mismatch",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription ="Invalid Request",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = str(ex),)
def changepassword(
    request: Request,
    user: Customer,
    response: Response,
    setting: Setting,
    db: Session,
    payload: ChangePasswordRequest,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started chnage pin for {user.firstname}"
        )
        if payload.password and payload.confirmPassword:
            if payload.password == payload.confirmPassword:
                user.password = util.get_password_hash(payload.password)
                userRecord = queries.update_user_agent_records(db=db,id=user.id,user=user)
                if userRecord:
                    background_task.add_task(notifyUser,db=db,title=f"Change Password", message=f"Change Password Successful",userId=user.id, setting=setting)
                    email_body = util.templates.TemplateResponse("success.html",{"request": request, "user": userRecord,"message":f"Password change Successful"},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=f"Change Password",toAddress=userRecord.email,)
                    response.status_code = status.HTTP_200_OK
                    return BaseResponse(
                        statusCode =str(status.HTTP_200_OK),
                       statusDescription = SUCCESS,
                    )
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = FAILED,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = "PIN mismatch",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription ="Invalid Request",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = str(ex),)