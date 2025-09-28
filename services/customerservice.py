
import logging
from sqlalchemy.orm import Session
from models.model import *
from pathlib import Path
from models.queries import queries,customerQuery
from datetime import datetime,timedelta
from services.notificationservice import notifyUser
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.support_ticket import *
from schemas.support_comment import *
import shutil
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,UploadFile
)

logger = logging.getLogger(__name__)

def profile(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
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
               statusDescription = SYSTEMBUSY, )
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
               statusDescription = SYSTEMBUSY, )
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
            to_otp = util.generateOTP()
            otpModel = OTPModel(
                otp=to_otp,
                servicename="ninVerification",
                user_id=user.id,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=5)))
            createdOtp = queries.create(db=db,model=otpModel)
            if createdOtp:
                email_body = util.templates.TemplateResponse("otp.html",{"request": request, "user": userRecord,"otp":to_otp},)
                background_task.add_task(
                        util.mailer,
                        str(email_body.body, "utf-8"),
                        setting=setting,
                        subject="NIN OTP Verification",
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
               statusDescription = SYSTEMBUSY,)
async def handleOTPVerification(
    request: Request,
    user: CustomerModel,
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
                        userRecord = queries.create(db=db,model=user)
                        if userRecord:
                            latestOtp.status = OTPStatusEnum.CLOSED
                            latestOtp.updated_at = current_datetime
                            createdOtp = queries.create(db=db,model=latestOtp)
                            if createdOtp:
                                background_task.add_task(notifyUser,db=db,title=f"{payload.action.capitalize()} Verification", message=f"Your {payload.action.capitalize()} Verification Successful",userId=user.id, setting=setting)
                                background_task.add_task(upgradeAccount,db=db,user=userRecord,setting=setting,request=request,background_task=background_task)
                                email_body = util.templates.TemplateResponse(
                                        "success.html",{"request": request, "user": userRecord,"message":f"Your {payload.action.capitalize()} Verification Successful"},
                                    )
                                background_task.add_task(
                                        util.mailer,
                                        str(email_body.body, "utf-8"),
                                        setting=setting,
                                        subject=f"{payload.action.capitalize()} Verification Successful",
                                        toAddress=user.email,
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
               statusDescription = SYSTEMBUSY,)
async def changepin(
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
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SYSTEMBUSY,)
async def changepassword(
    request: Request,
    user: CustomerModel,
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
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SYSTEMBUSY,)
async def updateNextOfKin(
        payload: NextOfKinRequest,
    request: Request,
    user: CustomerModel,
    response: Response,
    setting: Setting,
    db: Session,
    background_task: BackgroundTasks,
):
    try:
        logger.info(
            f"started updating next of kin of account {user.firstname} with {payload.model_dump_json()}"
        )
        user.next_of_kin_address = payload.address
        user.next_of_kin_name=payload.fullName
        user.next_of_kin_phone = util.formatPhone(payload.phone)
        user.next_of_kin_relationship = payload.relationship
        user.is_next_of_kin = True
        userRecord = queries.create(db=db,model=user)
        if userRecord:
            email_body = util.templates.TemplateResponse("success.html",{"request": request, "user": userRecord,"message":f"Your Next of Kin details was submitted successfuly."},)
            background_task.add_task(upgradeAccount,db=db,user=userRecord,setting=setting,request=request,background_task=background_task)
            background_task.add_task(notifyUser,db=db,title=f"Next Of Kin Update", message=f"Your Next of Kin details was submitted successfuly.",userId=user.id, setting=setting)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Next Of Kin",toAddress=user.email,)
            response.status_code = status.HTTP_200_OK
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = UPDATEACCTERR,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SYSTEMBUSY, )
def upgradeAccount(db:Session,user:CustomerModel,setting:Setting,request:Request,background_task:BackgroundTasks):
    try:
        if user.bvn_verified and user.nin_verified and user.email_verified:
            user.account_type = AccountEnum.MERCHANT
            user.account_ratings = AccountRatingEnum.SILVER
            updated = queries.create(db=db, model=user)
            if updated:
                background_task.add_task(notifyUser,db=db,title=f"Account Upgrade", message=ACCOUNTUPGRADE,userId=user.id, setting=setting)
                role = queries.getRoleByTag(db=db,tag=AdminRoleEnum.BUSINESS)
                if role:
                    password = util.generateOTP()
                    merchant = AdminModel(
                    firstname=user.firstname,
                    lastname=user.lastname,
                    phonenumber=user.phonenumber,
                    email=user.email,
                    customer_id=user.id,
                    password=util.get_password_hash(password),
                    role_id=role.id,
                    status=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    preference =UserNotificationPreference(
                receive_via_email = True,
                receive_in_app = True,
                created_at=datetime.now()
            )
                )
                    queries.create(db=db, model=merchant)
                    email_body = util.templates.TemplateResponse(
                        "success.html",
                        {"request": request, "user": user,"message":ACCOUNTUPGRADE.replace("<password>",password).replace("<username>",user.email)},
                    )
                    background_task.add_task(
                        util.mailer,
                        str(email_body.body, "utf-8"),
                        setting=setting,
                        subject="Account Upgrade Successful",
                        toAddress=user.email,
                    )
                return updated
        return None
    except Exception as ex:
        logger.info(ex)
        return None
async def uploadProfileImage(response: Response,db:Session,user:CustomerModel,setting:Setting,request:Request,background_task:BackgroundTasks,img: UploadFile,
):
    try: #
        logger.info(
            f"started uploading profile image for {user.firstname} at {datetime.now()}"
        )
        logger.info(img.content_type)
        if img.content_type.startswith("image/"):
            UPLOAD_DIR = Path("templates/profiles")
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            if user.profile_picture:
                filename = Path(user.profile_picture).name
                logger.info(filename)
                file_path = UPLOAD_DIR / filename 
                logger.info(file_path)
                if file_path.exists():
                    file_path.unlink()
            file_ext = img.filename.split(".")[-1]
            unique_name = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = UPLOAD_DIR / unique_name
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            image_url = f"profiles/{unique_name}"
            user.profile_picture = image_url
            user.updated_at = datetime.now()
            saved = queries.create(db=db,model=user)
            return  BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Image",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def listOfSupportTickets(request: Request,response: Response,setting: Setting,db: Session,user: CustomerModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying support tickets list"
        )
        return SupportTicketsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.supportTickets(db=db,userId=user.id)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SupportTicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def openSupportTicket(response: Response,db:Session,user:CustomerModel,setting:Setting,request:Request,background_task:BackgroundTasks,payload:SupportTicketRequest,attachment: UploadFile,
):
    try: #
        logger.info(
            f"started uploading profile image for {user.firstname} at {datetime.now()}"
        )
        support = SupportTicketModel(
                user_id = user.id ,
                subject =payload.subject,
                description = payload.description,
                priority = PriorityEnum(payload.priority),
                status =OTPStatusEnum(payload.status),
                created_at = datetime.now(),
                updated_at = datetime.now()
            )
        logger.info(attachment.content_type)
        if attachment.content_type.startswith("image/"):
            UPLOAD_DIR = Path("templates/tickets")
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            file_ext = attachment.filename.split(".")[-1]
            unique_name = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = UPLOAD_DIR / unique_name
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(attachment.file, buffer)
            image_url = f"tickets/{unique_name}"
            support.attachment = image_url
        saved = queries.create(db=db,model=support)
        if saved:
            return  BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Support ticket failed",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addSupportTicketComment(response: Response,db:Session,user:CustomerModel,setting:Setting,request:Request,background_task:BackgroundTasks,payload:SupportTicketCommentRequest,attachment: UploadFile,
):
    try: #
        logger.info(
            f"started commenting on ticket {payload.ticket_id} for {user.firstname} at {datetime.now()}"
        )
        img = None
        logger.info(attachment.content_type)
        if attachment.content_type.startswith("image/"):
            UPLOAD_DIR = Path("templates/tickets")
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            file_ext = attachment.filename.split(".")[-1]
            unique_name = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = UPLOAD_DIR / unique_name
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(attachment.file, buffer)
            image_url = f"tickets/{unique_name}"
            img = image_url
        comment = TicketCommentModel(ticket_id = payload.ticket_id,user_id = user.id,comment = payload.comment,created_at = payload.created_at,attachment=img)
        saved = queries.create(db=db,model=comment)
        if saved:
            return  BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Support ticket failed",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)

# admin service
def listOfCustomer(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying customers from {startDate} to {endDate}"
        )
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            return CustomersResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=customerQuery.listAllCustomers(db=db,userId=admin.id,startDate=startDate,endDate=endDate)
            )
        else:
            return CustomersResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=customerQuery.listAllCustomers(db=db,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
