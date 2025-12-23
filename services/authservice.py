import json
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import authQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from services import notificationservice
from schemas.device import Device
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)

async def createAccount(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        payload: CustomerRequest,
        background_task: BackgroundTasks,):
    try:
        user = authQuery.userByEmailOrPhone(db=db,email=payload.email,phonenumber=payload.phonenumber)
        if user:
            if user.email == payload.email:
                if util.formatPhone(user.phonenumber) == util.formatPhone(payload.phonenumber):
                    if user.account_status == AccountStatusEnum.REG:
                        return await createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response,customer=user)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Device already register with another account",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Device already register with another account",)
        else:
            return await createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def createUserAccount(db: Session,setting: Setting,payload: CustomerRequest, background_task: BackgroundTasks, request: Request,response: Response,customer:CustomerModel=None):
    if customer:
        logger.info(f"Started resending verification for user {payload.email} {customer.account_status}")
        customer.firstname = payload.firstname
        customer.lastname = payload.lastname
        customer.password = util.get_password_hash(password=payload.password)
        customer.username = payload.username
        customer.updated_at = datetime.now()
        updatedUser = authQuery.create_account(db=db,user=customer)
        if not updatedUser:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        latestOtp = authQuery.get_latest_otp(db=db,userId=customer.id)
        if latestOtp:
            if latestOtp.expired_at > datetime.now():
                authToken = util.create_access_token(setting=setting,credentials={"username": customer.email,"password": latestOtp.otp},exp=60)
                if authToken:
                    device = json.loads(request.headers.get("device")) if request.headers.get("device") else {}
                    email_body = util.templates.TemplateResponse("otp.html",{"request": request,"device": device,"user": customer,"otp":latestOtp},)
                    background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject=f"Verification",
                    toAddress=customer.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=f"Please enter the OTP sent to {util.mask_email(customer.email)} to complete your registration",data={"token":authToken[0],"expires":authToken[1]})
            return await generateAndSendOTP(request=request,db=db,response=response,setting=setting,customer=customer,background_task=background_task)
        else:
            return await generateAndSendOTP(request=request,db=db,response=response,setting=setting,customer=customer,background_task=background_task)
    else:
        user = CustomerModel(
            identifier=util.generateId(length=6),
            firstname=payload.firstname,
            lastname=payload.lastname,
            email=payload.email,
            phonenumber=payload.phonenumber,
            username=payload.username,
            password=util.get_password_hash(password=payload.password),
            )
        createdAccount = authQuery.create_account(db=db, user=user)
        if createdAccount:
            return await generateAndSendOTP(request=request,db=db,setting=setting,background_task=background_task,response=response,customer=createdAccount)
async def generateAndSendOTP(request: Request,db: Session,setting: Setting,background_task:BackgroundTasks,response: Response,customer:CustomerModel):
    newOtp = authQuery.create_otp(db=db,otp=OTPModel(otp=util.generateOTP(), servicename="openAccount", user_id=customer.id,
                created_at=datetime.now(),expired_at=(datetime.now() + timedelta(minutes=15)),updated_at=datetime.now(),))
    if newOtp:
        authToken = util.create_access_token(setting=setting,credentials={"username": customer.email,"password": newOtp.otp},exp=60)
        if authToken:
            device = json.loads(request.headers.get("device")) if request.headers.get("device") else {}
            email_body = util.templates.TemplateResponse("otp.html",{"request": request,"device": device,"user": customer,"otp":newOtp},)
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
                wallet = AccountModel(user_id=user.id,walletAccount=util.formatPhoneShort(user.phonenumber),availableBalance="0",referenceNo=util.formatPhoneShort(user.phonenumber),accountStatus=AccountStatusEnum.ACTIVE,created_at = datetime.now(),updated_at = datetime.now())
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
async def create_pin(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: CustomerModel,
    payload: CreatePINRequest,
    device:Device,
    background_task: BackgroundTasks,):
    try:
        if user.pin:
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="PIN already exist",)
        if payload.pin == payload.confirmPin:
            user.pin = util.get_password_hash(password=payload.pin)
            user.updated_at = datetime.now()
            user.device = DeviceModel(
                            imeiNo = device.imeiNo,
                            modelName = device.modelName,
                            manufacturer = device.manufacturer,
                            deviceName = device.deviceName,
                            apiLevel = device.apiLevel,
                            isPhysicalDevice = device.isPhysicalDevice,
                            platformVersion = device.platformVersion,
                        )
            user.preference = UserNotificationPreference(
                receive_via_email = True,
                receive_in_app = True,
                created_at=datetime.now()
            )
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
                    device = json.loads(request.headers.get("device")) if request.headers.get("device") else {}
                    email_body = util.templates.TemplateResponse("otp.html",{"request": request,"device": device,"user": user,"otp":createdOTP},)
                    background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject=f"Password Reset",
                    toAddress=user.email,)
                    #background_task.add_task(util.sendMail,setting=setting, subject=f"Password Reset",toAddress=user.email, templatekey="2d6f.20c6e93ebf814272.k1.17ca5a70-7221-11f0-b2b9-525400a229b1.1987b43b197",template_data={"name":user.firstname,"OTP":createdOTP.otp})
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
async def login(request:Request,db: Session,response: Response,setting: Setting, payload: LoginRequest,device:Device,background_task: BackgroundTasks,):
    user = authQuery.userByEmailOrPhone( db=db,email=payload.username,phonenumber=util.formatPhoneWithDialingCode(payload.username))
    if user:
        if user.device and user.device.imeiNo == device.imeiNo:
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
            return BaseResponse(statusCode=str(status.HTTP_401_UNAUTHORIZED),statusDescription=DEVICEMISMATCH)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
async def deviceUnlockInitiate(
        payload:UnlockRequest,
        device:Device,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        background_task: BackgroundTasks,
):
    try:
        logger.info(f"started device unlock @ {datetime.now()}................")
        account = authQuery.userByEmailOrPhone(db=db,email=payload.username,phonenumber=util.formatPhoneWithDialingCode(payload.username))
        if account:
            logger.info(f"Verify user with transaction PIN @  {datetime.now()}.....................")
            if account.pin and util.verify_password(payload.pin,account.pin):
                logger.info(f"Account is fine go and check bvn/nin @  {datetime.now()}.....................")
                if payload.action.lower() == "unlock":
                    otp = util.generateOTP()
                    password = f"{otp}|{device.imeiNo}|{device.modelName}|{device.manufacturer}"
                    newOtp = OTPModel(otp=otp,user_id=account.id,status=OTPStatusEnum.OPEN,servicename="unlockInitiate",created_at=datetime.now(),expired_at=datetime.now()+timedelta(minutes=5),updated_at=datetime.now(),)
                    createdOTP = authQuery.create_otp(db=db,otp=newOtp)
                    email_body = util.templates.TemplateResponse("otp.html",{"request": request,"device": device,"user": account,"otp":createdOTP},)
                    background_task.add_task(
                    util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=f"Unlock Device Verification",toAddress=account.email,)
                    authToken = util.create_access_token(setting=setting,credentials={"username":account.phonenumber,"password": password,},exp=15,)
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"token":authToken[0],"expire":authToken[1],"message":f"Please enter the OTP sent to {util.mask_email(account.email)} to unlock your device"},)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
            else:
                logger.info(f"sending invalid transaction PIN to unlock device @ {datetime.now()}.....................")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDPIN)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription= SYSTEMBUSY)
async def deviceUnlockFinal(request: Request,device:Device,db:Session,response:Response,token:str,setting: Setting, background_task: BackgroundTasks,payload:OTPRequest):
    try:
        logger.info(f"Started verifying device unlock @ {datetime.now()} ..........")
        data = util.jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        logger.info(f"checking token {data} for device unlock @ {datetime.now()}.........")
        if data:
            user =authQuery.userByEmailOrPhone(db=db,email=data["username"],phonenumber=data["username"])
            if user:
                logger.info(f"Started verifying device verification details........{data['password']} and {payload.otp}")
                auth = str(data["password"]).split("|")
                if auth[0] == payload.otp and auth[1] == device.imeiNo and auth[2] == device.modelName and auth[3] == device.manufacturer:
                    otp = authQuery.get_otp_by_code(db=db,code=payload.otp,userId=user.id)
                    if otp and otp.expired_at > datetime.now():
                        logger.info(f"device unlock with valid OTP @ {datetime.now()}........")
                        user.device = DeviceModel(
                            imeiNo = device.imeiNo,
                            modelName = device.modelName,
                            manufacturer = device.manufacturer,
                            deviceName = device.deviceName,
                            apiLevel = device.apiLevel,
                            isPhysicalDevice = device.isPhysicalDevice,
                            platformVersion = device.platformVersion,
                        )
                        user.updated_at = datetime.now()
                        otp.status = OTPStatusEnum.CLOSED
                        otp.updated_at = datetime.now()
                        user.otps.append(otp)
                        updatedUser = authQuery.create_account(db=db,user=user)
                        response.status_code = status.HTTP_200_OK
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Device unlocked Successfully",)
                    else:
                        logger.info(f"otp already expired for device @ {datetime.now()}........")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=OTPEXPIRE)
                else:
                    logger.info(f"suspected fraud to unlock user device @ {datetime.now()}........")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
            else:
                logger.info("device unlock from suspicious user........")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unauthoried",)
        else:
            logger.info(f"device unlock without valid token")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNABLE)
    except util.jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="OTP has expired. Please request a new one",)  
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
