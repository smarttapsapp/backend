
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.model import *
from pathlib import Path
import shutil
from models.queries import authQuery,queries,adminQuery,customerQuery
from datetime import datetime,timedelta
from schemas import otp
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.cashout import *
from schemas.customer import *
from schemas.role import *
from schemas.product import *
from schemas.product_type import *
from schemas.admin import *
from schemas.station import *
from schemas.seat import *
from schemas.schedule import *
from schemas.payment import *
from schemas.route import RoutesResponse,AddRouteRequest
from schemas.bus_route import BusRoutesResponse,AddBusRouteRequest
from services.notificationservice import notifyUser
from services import productservice
from schemas.ticket import TicketsResponse,TicketResponse
from schemas.bus import BusesResponse,AddBusRequest
from schemas.park import ParksResponse
from schemas.train import *
from schemas.notification import *
from schemas.support_ticket import *
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,UploadFile
)

logger = logging.getLogger(__name__)

async def createAccount(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        payload: CreateAdminRequest,
        background_task: BackgroundTasks,):
    try:
        if payload.id:
            logger.info(f"updating user {payload.firstname} at {str(datetime.now())}")
            user = authQuery.getCheckAdmin(db=db,username=payload.email)
            if user:
                user.firstname = payload.firstname
                user.identifier = payload.identifier if payload.identifier else user.identifier
                user.lastname = payload.lastname
                user.phonenumber = payload.phonenumber
                user.email = payload.email
                user.companyName = payload.companyName
                user.companyAddress = payload.companyAddress
                user.provider_auth = payload.provider_auth
                user.provider_url = payload.provider_url
                user.updated_at = datetime.now()
                updatedUser = authQuery.create_account(db=db,user=user)
                if updatedUser:
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ACCTERROR)
        else:
            logger.info(f"creating new user {payload.firstname} at {str(datetime.now())}")
            user = authQuery.getCheckAdmin(db=db,username=payload.email)
            if user:
                response.status_code = status.HTTP_302_FOUND
                return BaseResponse(statusCode=str(status.HTTP_302_FOUND),statusDescription="Account already exist with the same details",)
            else:
                return await createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
async def authenticate_user(
        request:Request,
        db: Session,
    response: Response,
    setting: Setting,
    background_task: BackgroundTasks, payload: AdminLoginRequest):
    user = authQuery.getCheckAdmin(username=payload.username, db=db)
    if user:
        if util.verify_password(payload.password, user.password) is True:
            if user.status:
                authToken = util.create_access_token(setting=setting,credentials={"username": user.email,"password": payload.password,},exp=600)
                logger.info(authToken)
                return BaseResponse(
                    statusCode= str(status.HTTP_200_OK),
                    statusDescription= SUCCESS,
                    data={
                        "user":Admin.model_validate(user),
                        "idToken":authToken[0],
                        "expiresIn":authToken[1]
                    },
                
            )
            response.status_code= status.HTTP_400_BAD_REQUEST
            return BaseResponse(
        statusCode=str(status.HTTP_400_BAD_REQUEST),
        statusDescription=ACCTERROR
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
        statusCode=str(status.HTTP_400_BAD_REQUEST),
        statusDescription=INVALIDACCOUNT
        )
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(
        statusCode=str(status.HTTP_400_BAD_REQUEST),
        statusDescription=INVALIDACCOUNT
        )
async def verifyAccountOpening(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Customer,
    payload: OTPRequest,
    background_task: BackgroundTasks,):
    try:
        logger.info(user.otps)
        latestOTP:otp.OTP = sorted(user.otps, key=lambda p: p.id, reverse=True)[0]
        if latestOTP:
            logger.info(latestOTP)
            current_datetime = datetime.now()
            if latestOTP.expired_at >= current_datetime:
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=f"Account already created",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="User OTP failed or expired",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription= SYSTEMBUSY)
async def createUserAccount(db: Session,setting: Setting,payload: CreateAdminRequest, background_task: BackgroundTasks, request: Request,response: Response):
    try:
        logger.info("started creating new admin account")
        role = adminQuery.getRoleViaTag(db=db,tag=payload.tag)
        if role:
            password = util.generate_password()
            logger.info(f"New admin created {payload.firstname} with password {password}")
            newAdmin = AdminModel(
                    firstname=payload.firstname,
                    lastname=payload.lastname,
                    phonenumber=payload.phonenumber,
                    email=payload.email,
                    companyName = payload.companyName,
                    companyAddress = payload.companyAddress,
                    provider_auth = payload.provider_auth,
                    provider_url = payload.provider_url,
                    identifier=payload.identifier if payload.identifier else util.generateBillerId(),
                    password=util.get_password_hash(password),
                    role_id=role.id,
                    status=True,
                    cashout_enabled=False,
                    cashout_limit=10000000,
                    billerId = util.generateBillerId(),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    wallet=AccountModel(walletAccount=util.formatPhoneShort(payload.phonenumber),accountStatus=AccountStatusEnum.ACTIVE,availableBalance=0,created_at=datetime.now(),updated_at=datetime.now(),
                    cashout_enabled=False,
                    cashout_limit=10000000),
                    preference =UserNotificationPreference(
                receive_via_email = True,
                receive_in_app = True,
                created_at=datetime.now()
            )
                )
            createdAccount = adminQuery.create(db=db, model=newAdmin)
            if createdAccount:
                if role.tag in [AdminRoleEnum.BUSPROVIDER, AdminRoleEnum.TRAINPROVIDER]:
                    product = adminQuery.getProductByVas(db=db,vas="transport")
                    if product:
                        addproduct = AddProductTypeRequest(
                            billerId=newAdmin.billerId,
                            billerName=f"{newAdmin.lastname} {newAdmin.firstname}",
                            billerType="transport",
                            product_id=product.id,customerField="Phone Number",
                            hasAddons=False,hasLookup=False,hasPackages=False,
                            status=True,
                            )
                        await productservice.addBiller(db=db,setting=setting,payload=addproduct, background_task=background_task, request=request,response=response,admin=newAdmin)
                email_body = util.templates.TemplateResponse(
                    "onboarding.html",
                    {"request": request, "user": newAdmin,"password":password},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject="Onboarding Notification",
                    toAddress=newAdmin.email,
                )
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ACCTERROR)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ACCTERROR)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=CREATEACCTERR)    
def updateAccount(db: Session,setting: Setting,payload: CreateAdminRequest, background_task: BackgroundTasks, request: Request,response: Response):
    try:
        logger.info("started creating new admin account")
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            password = util.generate_password()
            newAdmin = AdminModel(
                    firstname=payload.firstname,
                    lastname=payload.lastname,
                    phonenumber=payload.phonenumber,
                    email=payload.email,
                    password=util.get_password_hash(password),
                    role_id=role.id,
                    status=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            createdAccount = adminQuery.create(db=db, model=newAdmin)
            if createdAccount:
                email_body = util.templates.TemplateResponse(
                    "onboarding.html",
                    {"request": request, "user": newAdmin,"password":password},
                )
                background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject="Onboarding Notification",
                    toAddress=newAdmin.email,
                )
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ACCTERROR)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ACCTERROR)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=CREATEACCTERR)
def sendSms(otp: OTPModel,response: Response,setting: Setting, background_task: BackgroundTasks):
    #latestOtp = authQuery.get_latest_otp(db=db, userId=userId)
    if otp:
        logger.info(otp)
        logger.info(otp.user)
        background_task.add_task(util.send_sms_message,setting=setting,toPhoneNumber=otp.user.phonenumber,message=f"Your activation code is {otp.otp}",transactionId=util.generateId())
        authToken = util.create_access_token(
            setting=setting,
            credentials={
                "username": otp.user.phonenumber,
                "password": otp.otp,
                },
                exp=5,
                )
        response.status_code = status.HTTP_200_OK
        return BaseResponse(
            statusCode=str(status.HTTP_200_OK),
            statusDescription=f"Please enter the OTP sent to {otp.user.phonenumber[0:4]}xxxxxx{otp.user.phonenumber[-2:]} to complete your registration",
            data={
                "idToken":authToken[0],
                "expiresIn":authToken[1]},
        )
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(
        statusCode=str(status.HTTP_400_BAD_REQUEST),
        statusDescription="OTP Issue. Try after sometime"
    )
def generateAndSendOTP(db: Session, userId:int,setting: Setting,background_task:BackgroundTasks,response: Response):
    newOtp = authQuery.create_otp(db=db,otp=OTPModel(otp=util.generateOTP(), servicename="openAccount", user_id=userId,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=15)),
            updated_at=datetime.now(),))
    if newOtp:
        return sendSms(otp=newOtp,background_task=background_task,response=response,setting=setting)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription="Unable to send otp at the moment",
            )
async def authenticateUser(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    background_task: BackgroundTasks, 
    payload: AdminLoginRequest,):
    try:
        logger.info(f"started authentication for {payload.username}")
        user = authQuery.getCheckAdmin(username=payload.username, db=db)
        logger.info(user.lastname)
        if user:
            if util.verify_password(payload.password, user.password):
                authToken = util.create_access_token(setting=setting,credentials={"username": user.email,"password": payload.password},exp=60)
                response.set_cookie(
                    key="access_token",
                    value=authToken[0],
                    expires=authToken[1],
                    max_age=authToken[1], 
                    httponly=True, 
                    samesite="None",
                    path="/",
                      secure=True)
                return BaseResponse(
                    statusCode= str(status.HTTP_200_OK),
                    statusDescription= SUCCESS,
                
            )
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=INVALIDACCOUNT,
                )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=INVALIDACCOUNT,
                )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
async def profile(db: Session,
        request: Request,
        response: Response,
        setting: Setting,
        admin:AdminModel,):
    if admin:
        return BaseResponse(statusCode= str(status.HTTP_200_OK),statusDescription= SUCCESS,data=AdminProfile.from_orm(admin).model_dump())
def sendSms(otp: OTPModel,response: Response,setting: Setting, background_task: BackgroundTasks):
    #latestOtp = adminQuery.get_latest_otp(db=db, userId=userId)
    if otp:
        logger.info(otp)
        logger.info(otp.user)
        background_task.add_task(util.send_sms_message,setting=setting,toPhoneNumber=otp.user.phonenumber,message=f"Your activation code is {otp.otp}",transactionId=util.generateId())
        authToken = util.create_access_token(
            setting=setting,
            credentials={
                "username": otp.user.phonenumber,
                "password": otp.otp,
                },
                exp=5,
                )
        response.status_code = status.HTTP_200_OK
        return BaseResponse(
            statusCode=str(status.HTTP_200_OK),
            statusDescription=f"Please enter the OTP sent to {otp.user.phonenumber[0:4]}xxxxxx{otp.user.phonenumber[-2:]} to complete your registration",
            data={
                "idToken":authToken[0],
                "expiresIn":authToken[1]},
        )
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(
        statusCode=str(status.HTTP_400_BAD_REQUEST),
        statusDescription="OTP Issue. Try after sometime"
    )
def generateAndSendOTP(db: Session, userId:int,setting: Setting,background_task:BackgroundTasks,response: Response):
    newOtp = authQuery.create_otp(db=db,otp=OTPModel(otp=util.generateOTP(), servicename="openAccount", user_id=userId,tenant=tenant,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=15)),
            updated_at=datetime.now(),))
    if newOtp:
        return sendSms(otp=newOtp,background_task=background_task,response=response,setting=setting)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription="Unable to send otp at the moment",
            )
# resert password
async def resetPasswordInitiate(
    request: Request,
    user: Admin,
    response: Response,
    setting: Setting,
    db: Session,
    background_task: BackgroundTasks,
):
    try:
        logger.info(f"started resetPasswordInitiate")
        otp = util.generateOTP()
        dbOtp = OTPModel(
            otp=otp,
            user_id=user.id,
            status=OTPStatusEnum.OPEN,
            servicename="resetPasswordInitiate",
            created_at=datetime.now(),
            expired_at=datetime.now()+timedelta(minutes=5),
            updated_at=datetime.now(),
        )
        createdOTP = authQuery.create_otp(db=db, otp=dbOtp)
        if createdOTP:
            return sendSms(otp=createdOTP,response=response,setting=setting,background_task=background_task)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=SYSTEMBUSY,
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse.model_validate(
            {
                "statusCode": str(status.HTTP_400_BAD_REQUEST),
                "statusDescription": SYSTEMBUSY,
            }
        )
async def resetPasswordFinal(db:Session,response:Response,token:str,setting: Setting, background_task: BackgroundTasks,payload:ResetPasswordRequest):
    try:
        data = util.jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        if data:
            logger.info(data)
            user = authQuery.getOne(db=db,email=data["username"])
            logger.info(user)
            if user:
                if data["password"] == payload.otp:
                    otp = authQuery.get_otp_by_code(db=db,code=payload.otp,userId=user.id)
                    if otp and otp.expired_at > datetime.now():
                        if payload.password == payload.confirmPassword:
                            user.password = util.get_password_hash(payload.password)
                            user.updated_at = datetime.now()
                            otp.status = OTPStatusEnum.CLOSED
                            otp.updated_at = datetime.now()
                            updatedUser = authQuery.create_account(db=db,user=user)
                            if updatedUser:
                                updatedOtp = authQuery.updateOTPStatus(db=db,id=otp.id)
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
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid/expired OTP",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unauthoried",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unauthoried",)
    except util.JWTError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(e),)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def changeAdminPassword(request:Request,db:Session,response:Response,admin:AdminModel,setting: Setting,payload:ChangePasswordRequest, background_task: BackgroundTasks):
    try:
        if util.verify_password(payload.oldPassword,admin.password):
            if payload.password == payload.confirmPassword:
                admin.password = util.get_password_hash(payload.password)
                admin.updated_at = datetime.now()
                updatedAdmin = adminQuery.create(db=db,model=admin)
                if updatedAdmin:
                    email_temp = util.templates.TemplateResponse("change_password.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_temp.body, "utf-8"),setting=setting,subject="Change Password",toAddress=admin.email)
                    response.status_code = status.HTTP_200_OK
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Change Password Successful",)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to complete Password Change",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Error! Password mismatch",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Old Password",)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def uploadProfileImage(response: Response,db:Session,admin:AdminModel,setting:Setting,request:Request,background_task:BackgroundTasks,img: UploadFile,
):
    try: #
        logger.info(
            f"started uploading profile image for admin {admin.firstname} at {datetime.now()}"
        )
        logger.info(img.content_type)
        if img.content_type.startswith("image/"):
            UPLOAD_DIR = Path("templates/admin")
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            if admin.photo:
                filename = Path(admin.photo).name
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
            admin.photo = image_url
            admin.updated_at = datetime.now()
            saved = adminQuery.create(db=db,model=admin)
            return  BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription = SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Image",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
#analytics
async def analytics(
        admin:AdminModel,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session):
    try:
        customer = adminQuery.customersAnalytics(db=db)
        logger.info(f"this is the customer analytics {customer}")
        if customer:
            debit = adminQuery.debitPaymentsAnalytics(db=db)
            logger.info(f"this is the debit analytics {debit}")
            if debit:
                credit = adminQuery.creditPaymentsAnalytics(db=db)
                if credit:
                    return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),statusDescription= f"Successful",
                    data={
                        "customer":customer,
                        "debit":debit,
                        "credit":credit
                    },)
                else:
                    return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),statusDescription= SUCCESS,
                    data={
                        "customer":customer,
                        "debit":debit,
                        "credit":None
                    },)
            else:
                return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),statusDescription= SUCCESS,
                    data={
                        "customer":customer,
                        "debit":None,
                        "credit":None
                    },)
        else:
            return BaseResponse(
                    statusCode=str(status.HTTP_200_OK),statusDescription= SUCCESS,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
# admin service
async def listOfAdmins(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying admins")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ADMIN,AdminRoleEnum.ACCOUNTANT]:
            return AdminsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getAllAdmin(db=db))
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return AdminsResponse(statusCode= str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return AdminsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def listOfProviders(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying providers")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ADMIN,AdminRoleEnum.ACCOUNTANT]:
            return AdminsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getAdminProvider(db=db))
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return AdminsResponse(statusCode= str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return AdminsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# admin
async def listOfAdminsByRole(response: Response,db: Session,admin: AdminModel,role:str):
    try:
        logger.info(f"started querying {role}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ADMIN,AdminRoleEnum.ACCOUNTANT]:
            if role:
                existing = AdminTypeEnum(role.upper())
                if existing:
                    return AdminsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getAllAdminByRole(db=db,role=existing))
                return AdminsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getAdminProvider(db=db))
            return AdminsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=[])
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return BaseResponse(statusCode= str(status.HTTP_401_UNAUTHORIZED),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# roles
async def listOfRoles(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying products")
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return RolesResponse(statusCode= str(status.HTTP_401_UNAUTHORIZED),statusDescription=FAILED,)
        else:
            return RolesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getAllRole(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return AdminsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addRole(db: Session,setting: Setting,payload: AddRoleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new admin role @ {datetime.now()}")
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST)
        else:
            new = RoleModel(identifier=util.generateId(length=6),name=payload.name,tag=AdminRoleEnum(payload.tag),status=payload.status,description=payload.description,created_at=datetime.now(),updated_at=datetime.now(),)
            created = queries.create(db=db, model=new)
            if created:
                email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def updateRole(db: Session,setting: Setting,payload: AddRoleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new admin role @ {datetime.now()}")
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            role.name = payload.name
            role.tag =AdminRoleEnum(payload.tag)
            role.updated_at=datetime.now()
            created = queries.create(db=db, model=role)
            if created:
                email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteRole(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,roleId: int):
    try:
        logger.info(f"started deleting role {roleId} @ {datetime.now()}")
        role = adminQuery.deleteRole(db=db,roleId=roleId)
        if role:
            response.status_code = status.HTTP_200_OK
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# transport service
async def listOfParks(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(f"started querying buses")
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ParksResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SUCCESS,data=adminQuery.getParks(db=db,startDate=startDate,endDate=endDate))
        else:
            return ParksResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getParks(db=db,startDate=startDate,endDate=endDate))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ParksResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# buses
async def listOfBusRoutes(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying products")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return BusRoutesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getBusRoutes(db=db))
        else:
            return BusRoutesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getBusRoutes(db=db,adminId=admin.id))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusRoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addBusRoute(db: Session,setting: Setting,payload: AddBusRouteRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new route @ {datetime.now()}")
        if admin.role.tag in[AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
        #if admin.role.tag in [AdminRoleEnum.BUSINESS,AdminRoleEnum.SUPERADMIN]:
            existing = queries.getBusRouteByStartStopStation(db=db,start=payload.startId, stop=payload.stopId,adminId=admin.id)
            if existing:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST)
            else:
                startStation = adminQuery.getStationById(db=db,stationId=payload.startId)
                if startStation:
                    stopStation = adminQuery.getStationById(db=db,stationId=payload.stopId)
                    if stopStation:
                        #busess = adminQuery.getBusesByIds(db=db,ids=payload.buses)
                        #logger.info(busess)
                        #if busess:
                        previous = queries.getBusRouteById(db=db,routeId=payload.id)
                        if previous and previous.admin_id == admin.id:
                            #previous.buses = busess
                            previous.destinationStation_id=stopStation.id
                            previous.sourceStation_id=startStation.id
                            previous.updated_at = datetime.now()
                            previous.baseprice = int(payload.baseprice)*100
                        else:
                            previous = BusRouteModel(identifier=util.generateId(length=6),routeName=payload.routeName,sourceStation_id=startStation.id,destinationStation_id=stopStation.id,mode=startStation.mode,admin_id=admin.id,created_at=datetime.now(),updated_at=datetime.now(),baseprice=int(payload.baseprice)*100)
                        created = adminQuery.create(db=db, model=previous)
                        if created:
                            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Route Created",toAddress=admin.email,)
                            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                        #else:
                        #    response.status_code = status.HTTP_400_BAD_REQUEST
                        #    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOROUTE)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ENDSTATIONERR)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=STARTSTATIONERR)
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode = str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def listOfBuses(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(f"started querying buses")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return BusesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getBuses(db=db))
        else:
            return BusesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getBuses(db=db,adminId=admin.id))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addBus(db: Session,setting: Setting,payload: AddBusRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating/updating bus @ {datetime.now()}")
        if admin.role.tag in[AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
            busRoutes = []
            adminId = admin.id if admin.role.tag in [AdminRoleEnum.BUSPROVIDER] else None
            previous = adminQuery.getBus(db=db,busNumber=payload.bus_number)
            if previous:
                schedules = [BusScheduleModel(admin_id = admin.id,price = int(schedule['price'])*100,departureTime = schedule['departureTime'],arrivalTime = schedule['arrivalTime'],timeOfOperation = schedule['timeOfOperation'],created_at=datetime.now(),updated_at=datetime.now(),) for schedule in payload.schedules]
                logger.info(schedules)
                logger.info(previous.name)
                logger.info(previous.admin_id)
                logger.info(admin.id)
                previous.airCondition = payload.airCondition
                previous.tv = payload.tv
                previous.base_price = payload.base_price
                previous.camera = payload.camera
                previous.name = payload.name
                previous.bus_capacity=payload.bus_capacity
                previous.description = payload.description
                previous.billerId = admin.billerId
                previous.routes = busRoutes
                previous.updated_at = datetime.now()
            else:
                for route in payload.routes:
                    startStation = adminQuery.getStationById(db=db,stationId=route['departure'])
                    if startStation:
                        stopStation = adminQuery.getStationById(db=db,stationId=route['arrival'])
                        if stopStation:
                            busRoutes.append(BusRouteModel(identifier=util.generateId(length=6),routeName=f"{startStation.location} {stopStation.location}",sourceStation_id=startStation.id,destinationStation_id=stopStation.id,mode=startStation.mode,admin_id=admin.id,created_at=datetime.now(),updated_at=datetime.now(),isdelete=False,baseprice=int(route['price'])*100))
                if busRoutes:
                    schedules = [BusScheduleModel(identifier=util.generateId(length=6),admin_id =admin.id,price = int(schedule['price'])*100,departureTime = schedule['departureTime'],arrivalTime = schedule['arrivalTime'],timeOfOperation = schedule['timeOfOperation'],created_at=datetime.now(),updated_at=datetime.now(),isdelete=False,) for schedule in payload.schedules]
                    logger.info(schedules)
                    previous = BusModel(identifier=util.generateId(length=6),admin_id=admin.id,name=payload.name,bus_number=payload.bus_number,description=payload.description,tv=payload.tv,camera=payload.camera,airCondition=payload.airCondition,bus_capacity=payload.bus_capacity,base_price=int(payload.base_price)*100,availabilityStatus=BusStatusEnum.ACTIVE,created_at=datetime.now(),updated_at=datetime.now(),billerId=admin.billerId,isdelete=False,schedules=schedules,routes=busRoutes)
                    created = queries.create(db=db, model=previous)
                    if created:
                        email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                        background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                        return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ROUTEERROR)
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode = str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)   
async def editBus(db: Session,setting: Setting,payload: AddBusRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"Started updating bus {payload.bus_number} by {admin.email} at {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.BUSPROVIDER, AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=UNAUTHORISED)
        loggedInAdmin = admin
        if admin.role.tag in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            loggedInAdmin = queries.getAdminByIdentifier(db=db, adminId=payload.admin_id)
        # Check for existing bus
        existing = adminQuery.getBus(db=db,busNumber=payload.bus_number)
        if not existing:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(statusCode=str(status.HTTP_404_NOT_FOUND), statusDescription="Bus not found")
        if existing.admin_id != loggedInAdmin.id:
            response.status_code = status.HTTP_403_FORBIDDEN
            return BaseResponse(statusCode=str(status.HTTP_403_FORBIDDEN), statusDescription="Access denied")
        existing_schedules_map = {s.identifier: s for s in existing.schedules}
        existing_routes_map = {s.identifier: s for s in existing.routes}
        logger.info(f"Existing schedules map: {existing_schedules_map.items()}")
        logger.info(f"Existing Routes map: {existing_routes_map.items()}")
        logger.info(f"Payload schedules: {existing_schedules_map.keys()}")
        schedule_to_delete = [identifier for identifier in existing_schedules_map.keys() if identifier not in [s.get("identifier") for s in payload.schedules or []]]
        routes_to_delete = [identifier for identifier in existing_routes_map.keys() if identifier not in [s.get("identifier") for s in payload.routes or []]]
        logger.info(f"Schedule identifiers to delete: {schedule_to_delete}")
        logger.info(f"Routes identifiers to delete: {routes_to_delete}")
        updated_schedule_models = []
        if  payload.schedules:
            logger.info(f"Processing {len(payload.schedules)} schedules from payload")
            for schedule_data in payload.schedules:
                schedule_identifier = schedule_data.get("identifier")
                if schedule_identifier and schedule_identifier in existing_schedules_map:
                    #  Update existing schedule
                    schedule_obj = existing_schedules_map[schedule_identifier]
                    schedule_obj.departureTime = schedule_data["departureTime"]
                    schedule_obj.arrivalTime = schedule_data["arrivalTime"]
                    schedule_obj.timeOfOperation = schedule_data["timeOfOperation"]
                    schedule_obj.price = int(schedule_data["price"])*100
                    schedule_obj.updated_at = datetime.now()
                    updated_schedule_models.append(schedule_obj)
                else:
                    #  Add new schedule
                    new_schedule = BusScheduleModel(
                        identifier=schedule_identifier or util.generateId(length=6),
                        bus_id=existing.id,
                        admin_id=admin.id,
                        price = int(schedule_data["price"])*100,
                        departureTime=schedule_data["departureTime"],
                        arrivalTime=schedule_data["arrivalTime"],
                        timeOfOperation=schedule_data["timeOfOperation"],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    queries.create(db=db,model=new_schedule)
                    updated_schedule_models.append(new_schedule)
        logger.info(f"Updated schedules: {updated_schedule_models}")
        updated_routes = []
        if  payload.routes:
            logger.info(f"Processing {len(payload.routes)} routes from payload")
            for route in payload.routes:
                identifier = route.get("identifier")
                logger.info(f"{identifier} for processing")
                if identifier and identifier in existing_routes_map:
                    #  Update existing schedule
                    route_obj = existing_routes_map[identifier]
                    route_obj.baseprice=int(route['price'])*100
                    route_obj.updated_at = datetime.now()
                    updated_routes.append(route_obj)
                else:
                    startStation = adminQuery.getStationById(db=db,stationId=route['departure'])
                    if startStation:
                        stopStation = adminQuery.getStationById(db=db,stationId=route['arrival'])
                        if stopStation:
                            newRoute = BusRouteModel(
                                identifier=util.generateId(length=6),
                                bus_id=existing.id,
                                routeName=f"{startStation.location} {stopStation.location}",
                                sourceStation_id=startStation.id,
                                destinationStation_id=stopStation.id,
                                mode=startStation.mode,
                                admin_id=admin.id,
                                created_at=datetime.now(),
                                updated_at=datetime.now(),
                                isdelete=False,
                                baseprice=int(route['price'])*100)
                            queries.create(db=db,model=newRoute)
                            updated_routes.append(newRoute)
        logger.info(f"Updated routes: {updated_routes}")
        existing.name = payload.name
        existing.airCondition = payload.airCondition
        existing.tv = payload.tv
        existing.bus_capacity=payload.bus_capacity
        existing.availabilityStatus = payload.availabilityStatus
        existing.base_price = int(payload.base_price)*100
        existing.camera = payload.camera
        existing.description = payload.description
        if updated_schedule_models:
            existing.schedules = updated_schedule_models
        if updated_routes:
            existing.routes = updated_routes
        existing.updated_at = datetime.now()
        updated = adminQuery.create(db=db, model=existing)
        if updated:
            email_body = util.templates.TemplateResponse(
                "onboarding.html",
                {"request": request, "user": admin},
            )
            background_task.add_task(
                util.mailer,
                str(email_body.body, "utf-8"),
                setting=setting,
                subject="Bus Updated",
                toAddress=admin.email,
            )
            return BaseResponse(
                statusCode=str(status.HTTP_200_OK),
                statusDescription="Bus updated successfully",
            )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription="Failed to update bus",
        )
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteBus(db: Session,setting: Setting, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,busNumber: str):
    try:
        logger.info(f"started deleting bus {busNumber} @ {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.BUSPROVIDER, AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        bus = adminQuery.getBus(db=db, busNumber=busNumber)
        if not bus:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        if admin.role.tag in [AdminRoleEnum.BUSPROVIDER] and bus.admin_id != admin.id:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        bus.isdelete = True
        bus.updated_at = datetime.now()
        created = queries.create(db=db, model=bus)
        if created:
            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Delete Bus",toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="Bus deleted successfully")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# schedules
async def listOfSchedules(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying available schedules")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return SchedulesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getSchedules(db=db))
        else:
            return SchedulesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getSchedules(db=db,adminId=admin.id))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SchedulesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addSchedule(db: Session,setting: Setting,payload: AddScheduleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new schedule at {datetime.now()}")
        existing = adminQuery.getScheduleById(db=db,scheduleId=payload.id)
        if existing:
            existing.arrivalTime = payload.arrivalTime
            existing.departureTime = payload.departureTime
            existing.timeOfOperation = payload.timeOfOperation
        else:
            existing = ScheduleModel(
                identifier=util.generateId(length=6),
                admin_id = admin.id,
                timeOfOperation = payload.timeOfOperation,
                departureTime = payload.departureTime,
                arrivalTime = payload.arrivalTime,
                mode = payload.mode,
                created_at=datetime.now(),updated_at=datetime.now(),)
        created = queries.create(db=db, model=existing)
        if created:
            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Schedule",toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def updateSchedule(db: Session,setting: Setting,payload: AddRoleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new admin role @ {datetime.now()}")
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            role.name = payload.name
            role.tag =AdminRoleEnum(payload.tag)
            role.updated_at=datetime.now()
            created = queries.create(db=db, model=role)
            if created:
                email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteSchedule(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,scheduleId: int):
    try:
        logger.info(f"started deleting schedule {scheduleId} @ {datetime.now()}")
        schedule = adminQuery.deleteSchedule(db=db,scheduleId=scheduleId)
        if schedule:
            response.status_code = status.HTTP_200_OK
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# schedules
async def listOfSeats(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying available schedules")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return SeatsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getSeats(db=db))
        else:
            return SeatsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getSeats(db=db,adminId=admin.id))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SeatsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addSeat(db: Session,setting: Setting,payload: AddSeatRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new seat at {datetime.now()}")
        existing = adminQuery.getSeatById(db=db,seatId=payload.id)
        if existing:
            existing.price = payload.price
            existing.classType = TrainClassEnum[payload.classType]
        else:
            existing = SeatModel(
                admin_id = admin.id,
                seatNumber = 10,
                price = payload.price,
                classType = TrainClassEnum[payload.classType],
                availabilityStatus = "available",
                created_at=datetime.now(),updated_at=datetime.now(),)
        created = queries.create(db=db, model=existing)
        if created:
            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)       
async def deleteSeat(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,seatId: int):
    try:
        logger.info(f"started deleting seat {seatId} @ {datetime.now()}")
        role = adminQuery.deleteSeat(db=db,seatId=seatId)
        if role:
            response.status_code = status.HTTP_200_OK
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# trains
async def listOfTrains(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(f"started querying trains")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return TrainsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getTrains(db=db))
        else:
            return TrainsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getTrains(db=db,adminId=admin.id))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TrainsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addTrain(db: Session,setting: Setting,payload: AddTrainRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new train by {admin.email} at {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
            loggedInAdmin = admin
            if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
                loggedInAdmin = queries.getAdminByIdentifier(db=db,adminId=payload.admin_id)
            routes = adminQuery.getRoutesByIds(db=db,ids=payload.routes,adminId=loggedInAdmin.id)
            if routes:
                schedules = [TrainScheduleModel(identifier=util.generateId(length=6),admin_id =admin.id,departureTime = schedule['departureTime'],arrivalTime = schedule['arrivalTime'],timeOfOperation = schedule['timeOfOperation'],created_at=datetime.now(),updated_at=datetime.now(),) for schedule in payload.schedules]
                previous = TrainModel(identifier=util.generateId(length=6),admin_id=loggedInAdmin.id,trainNumber=payload.trainNumber,trainName=payload.trainName,description=payload.description,created_at=datetime.now(),updated_at=datetime.now(),isdelete=False,billerId=loggedInAdmin.billerId,schedules=schedules,routes=routes)
                created = queries.create(db=db, model=previous)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="New Train added successfully")
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOROUTE)
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode = str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def editTrain(db: Session,setting: Setting,payload: AddTrainRequest,background_task: BackgroundTasks,request: Request,response: Response,admin: AdminModel):
    try:
        logger.info(f"Started updating train {payload.trainNumber} by {admin.email} at {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.TRAINPROVIDER, AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode=str(status.HTTP_401_UNAUTHORIZED), statusDescription=UNAUTHORISED)
        loggedInAdmin = admin
        if admin.role.tag in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            loggedInAdmin = queries.getAdminByIdentifier(db=db, adminId=payload.admin_id)
        # Check for existing train
        existing = adminQuery.getTrain(db=db, trainNumber=payload.trainNumber)
        if not existing:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(statusCode=str(status.HTTP_404_NOT_FOUND), statusDescription="Train not found")
        if existing.admin_id != loggedInAdmin.id:
            response.status_code = status.HTTP_403_FORBIDDEN
            return BaseResponse(statusCode=str(status.HTTP_403_FORBIDDEN), statusDescription="Access denied")
        existing_schedules_map = {s.identifier: s for s in existing.schedules}
        logger.info(f"Existing schedules map: {existing_schedules_map.items()}")
        logger.info(f"Payload schedules: {existing_schedules_map.keys()}")
        obj_delete = [identifier for identifier in existing_schedules_map.keys() if identifier not in [s.get("identifier") for s in payload.schedules or []]]
        logger.info(f"Schedule identifiers to delete: {obj_delete}")
        updated_schedule_models = []
        deleted_schedule_models = []
        if  payload.schedules:
            logger.info(f"Processing {len(payload.schedules)} schedules from payload")
            for schedule_data in payload.schedules:
                schedule_identifier = schedule_data.get("identifier")
                if schedule_identifier and schedule_identifier in existing_schedules_map:
                    #  Update existing schedule
                    schedule_obj = existing_schedules_map[schedule_identifier]
                    schedule_obj.departureTime = schedule_data["departureTime"]
                    schedule_obj.arrivalTime = schedule_data["arrivalTime"]
                    schedule_obj.timeOfOperation = schedule_data["timeOfOperation"]
                    schedule_obj.updated_at = datetime.now()
                    updated_schedule_models.append(schedule_obj)
                else:
                    #  Add new schedule
                    new_schedule = TrainScheduleModel(
                        identifier=schedule_identifier or util.generateId(length=6),
                        train_id=existing.id,
                        admin_id=admin.id,
                        departureTime=schedule_data["departureTime"],
                        arrivalTime=schedule_data["arrivalTime"],
                        timeOfOperation=schedule_data["timeOfOperation"],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    queries.create(db=db,model=new_schedule)
                    updated_schedule_models.append(new_schedule)
        logger.info(f"Updated schedules: {updated_schedule_models}")
        # Update routes
        routes = adminQuery.getRoutesByIds(db=db, ids=payload.routes, adminId=loggedInAdmin.id)
        existing.trainName = payload.trainName
        existing.description = payload.description
        if updated_schedule_models:
            existing.schedules = updated_schedule_models
        adminQuery.deleteTrainSchedules(db=db,ids=obj_delete)
        db.commit()
        existing.routes = routes
        existing.updated_at = datetime.now()

        # Save changes
        updated = queries.create(db=db, model=existing)
        if updated:
            email_body = util.templates.TemplateResponse(
                "onboarding.html",
                {"request": request, "user": admin},
            )
            background_task.add_task(
                util.mailer,
                str(email_body.body, "utf-8"),
                setting=setting,
                subject="Train Updated",
                toAddress=admin.email,
            )
            return BaseResponse(
                statusCode=str(status.HTTP_200_OK),
                statusDescription="Train updated successfully",
            )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription="Failed to update train",
        )
    except Exception as ex:
        logger.error(f"Error updating train: {str(ex)}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
async def deleteTrain(db: Session,setting: Setting,background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,trainNumber:str):
    try:
        logger.info(f"started deleting role {trainNumber} @ {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.TRAINPROVIDER, AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        train = adminQuery.getTrain(db=db, trainNumber=trainNumber)
        if not train:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        if admin.role.tag in [AdminRoleEnum.TRAINPROVIDER] and train.admin_id != admin.id:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        train.isdelete = True
        train.updated_at = datetime.now()
        created = queries.create(db=db, model=train)
        if created:
            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="Train deleted successfully")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    except IntegrityError as e:
        logger.error(str(e))
        db.rollback()
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription="This train cannot be deleted because passengers have already booked tickets on it.")
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# routes
async def listOfRoutes(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying products")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return RoutesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getRoutes(db=db))
        else:
            return RoutesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getRoutes(db=db,adminId=admin.id))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addRoute(db: Session,setting: Setting,payload: AddRouteRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new route @ {datetime.now()}")
        if admin.role.tag in[AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
        #if admin.role.tag in [AdminRoleEnum.BUSINESS,AdminRoleEnum.SUPERADMIN]:
            startStation = adminQuery.getStationById(db=db,stationId=payload.startId)
            if startStation:
                stopStation = adminQuery.getStationById(db=db,stationId=payload.stopId)
                if stopStation:
                    existing = adminQuery.getRouteByStartStopStation(db=db,start=startStation.id, stop=stopStation.id,adminId=admin.id)
                    if existing and payload.id is None:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST)
                    else:
                        previous = adminQuery.getRouteById(db=db,routeId=payload.id)
                        if previous and previous.admin_id == admin.id:
                            previous.destinationStation_id=stopStation.id
                            previous.sourceStation_id=startStation.id
                            previous.updated_at = datetime.now()
                        else:
                            seatsm = [PricingModel(price = int(seat['price'])*100,classType = seat['classType'],availabilityStatus = "available",per_km_rate="0",created_at=datetime.now(),updated_at=datetime.now(),) for seat in payload.seats]
                            previous = TrainRouteModel(identifier=util.generateId(length=6),sourceStation_id=startStation.id,destinationStation_id=stopStation.id,admin_id=admin.id,created_at=datetime.now(),updated_at=datetime.now(),isdelete=False,prices=seatsm)
                        created = adminQuery.create(db=db, model=previous)
                        if created:
                            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Route Created",toAddress=admin.email,)
                            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="New Route Created Successfully")
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=ENDSTATIONERR)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=STARTSTATIONERR)
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode = str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def updateRoute(db: Session,setting: Setting,payload: AddRouteRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"Started updating route {payload.identifier} by {admin.email} at {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.TRAINPROVIDER, AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode=str(status.HTTP_401_UNAUTHORIZED), statusDescription=UNAUTHORISED)
        loggedInAdmin = admin
        if admin.role.tag in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            loggedInAdmin = queries.getAdminByIdentifier(db=db, adminId=payload.admin_id)
        # Check for existing route
        startStation = adminQuery.getStationById(db=db,stationId=payload.startId)
        if not startStation:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(statusCode=str(status.HTTP_404_NOT_FOUND), statusDescription=STARTSTATIONERR)
        stopStation = adminQuery.getStationById(db=db,stationId=payload.stopId)
        if not stopStation:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(statusCode=str(status.HTTP_404_NOT_FOUND), statusDescription=ENDSTATIONERR)
        existing = queries.getRouteByIdentier(db=db, routeId=payload.identifier)
        if not existing:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(statusCode=str(status.HTTP_404_NOT_FOUND), statusDescription=NOROUTE)
        if existing.admin_id != loggedInAdmin.id:
            response.status_code = status.HTTP_403_FORBIDDEN
            return BaseResponse(statusCode=str(status.HTTP_403_FORBIDDEN), statusDescription=UNAUTHORISED)
        existing_prices_map = {s.id: s for s in existing.prices}
        updated_price_models = []
        for seat in payload.prices:
            priceId = seat.get("id")
            if priceId and priceId in existing_prices_map:
                obj = existing_prices_map[priceId]
                obj.price = seat["price"]
                obj.classType = seat["classType"]
                obj.updated_at = datetime.now()
                updated_price_models.append(obj)
            else:
                #  Add new price
                newPrice = PricingModel(price = int(seat['price'])*100,classType = seat['classType'],availabilityStatus = "available",per_km_rate="0",created_at=datetime.now(),updated_at=datetime.now(),)
                queries.create(db=db,model=newPrice)
                updated_price_models.append(newPrice)
        existing.prices = updated_price_models
        existing.destinationStation_id = stopStation.id
        existing.sourceStation_id = startStation.id
        existing.updated_at = datetime.now()
        updated = queries.create(db=db, model=existing)
        if updated:
            email_body = util.templates.TemplateResponse(
                "onboarding.html",
                {"request": request, "user": admin},
            )
            background_task.add_task(
                util.mailer,
                str(email_body.body, "utf-8"),
                setting=setting,
                subject="Route Updated",
                toAddress=admin.email,
            )
            return BaseResponse(
                statusCode=str(status.HTTP_200_OK),
                statusDescription="Route updated successfully",
            )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription="Failed to update Route",
        )
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteRoute(db: Session,setting: Setting, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,routeId: int):
    try:
        logger.info(f"started deleting route {routeId} @ {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.TRAINPROVIDER, AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        route = queries.getRouteByIdentier(db=db, routeId=routeId)
        if not route:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        if admin.role.tag in [AdminRoleEnum.TRAINPROVIDER] and route.admin_id != admin.id:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        route.isdelete = True
        route.updated_at = datetime.now()
        created = queries.create(db=db, model=route)
        if created:
            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Delete Route",toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="Route deleted successfully")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# stations
async def listOfStations(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,mode:MovableEnum):
    try:
        logger.info(f"started querying products")
        if admin.role.tag in[AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER]:
            return StationsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getstations(db=db,mode=mode,adminId=admin.id))
        else:
            return StationsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getstations(db=db,mode=mode))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addStation(db: Session,setting: Setting,payload: AddStationRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating/updating new station @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
            if admin:
                if payload.identifier:
                    existing = queries.getStationById(db=db,stationId=payload.identifier)
                    if existing:
                        logger.info(existing)
                        if existing.long is None:
                            geo = util.get_lat_lon(location_name=payload.location)
                            existing.lat = geo[0]
                            existing.long = geo[1]
                        if existing.identifier is None:
                            existing.identifier=util.generateId(length=6)
                        existing.stationName = payload.stationName
                        existing.location = payload.location
                else:
                    geo = util.get_lat_lon(location_name=payload.location)
                    if geo:
                        existing = StationModel(
                            identifier=util.generateId(length=6),
                                    admin_id = admin.id,
                                    stationName = payload.stationName,
                                    location =  payload.location,
                                    description = f"{payload.stationName} {payload.location}",
                                    parkImage = payload.location,
                                    address = f"{payload.stationName} {payload.location}",
                                    contact = admin.phonenumber,
                                    policy = "",
                                    status = True,
                                    long = geo[1],
                                    lat =geo[0],isdelete=False,
                                    mode= TicketModeEnum(payload.mode) )
                created = queries.create(db=db,model=existing)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Station",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="Added/Updated Station successfully")
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def updateStation(db: Session,setting: Setting,payload: AddRoleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new admin role @ {datetime.now()}")
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            role.name = payload.name
            role.tag =AdminRoleEnum(payload.tag)
            role.updated_at=datetime.now()
            created = queries.create(db=db, model=role)
            if created:
                email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteStation(db: Session,setting: Setting, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,stationId: int):
    try:
        logger.info(f"started deleting station {stationId} @ {datetime.now()}")
        if admin.role.tag not in [AdminRoleEnum.TRAINPROVIDER, AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.ADMIN, AdminRoleEnum.SUPERADMIN]:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        station = queries.getStationById(db=db, stationId=stationId)
        if not station:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        if admin.role.tag in [AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.BUSPROVIDER,] and station.admin_id != admin.id:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
        station.isdelete = True
        station.updated_at = datetime.now()
        created = queries.create(db=db, model=station)
        if created:
            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Delete Station",toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription="Station deleted successfully")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    

async def listOfTickets(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying tickets list from {startDate} to {endDate}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return TicketsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=adminQuery.getTicketHistories(db=db,startDate=startDate,endDate=endDate)
            )
        else:
            return TicketsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=adminQuery.getTicketHistories(db=db,adminId=admin.id,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getTicketDetail(ticketId: int,response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(
            f"started querying ticket for ID {ticketId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            ticket = adminQuery.getTicketById(db=db,ticketId=ticketId)
            if ticket:
                return TicketResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=ticket)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)

# notifications
async def listOfNotifications(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying tickets list from {startDate} to {endDate}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return NotificationsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=adminQuery.getNotificationHistories(db=db,startDate=startDate,endDate=endDate)
            )
        else:
            return NotificationsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=adminQuery.getNotificationHistories(db=db,adminId=admin.id,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return NotificationsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def listOfProduct(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying products")
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        else:
            return ProductsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getProducts(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def listOfBiller(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying billers")
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        else:
            return ProductTypesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getProductBillers(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# payment
async def paymentsAnalytics(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(
            f"started querying payments last 10 days"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return PaymentsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=[Payment.from_orm(p).model_dump() for p in queries.getPaymentsLastTenDays(db=db)])
        else:
            return PaymentsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=[Payment.from_orm(p).model_dump() for p in queries.getPaymentsLastTenDays(db=db,adminId=admin.id)] )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# payment
async def ticketsAnalytics(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(
            f"started querying ticket last 10 days"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return TicketsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getTicketsLastTenDays(db=db))
        else:
            return TicketsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getTicketsLastTenDays(db=db,adminId=admin.id) )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# payment
async def cashOutsAnalytics(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(
            f"started querying cashout last 10 days"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return CashoutsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getCashoutsLastTenDays(db=db))
        else:
            return CashoutsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getCashoutsLastTenDays(db=db,adminId=admin.id) )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def listOfSupportTickets(response: Response,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying tickets list from {startDate} to {endDate}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return SupportTicketsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=adminQuery.getSupportTickets(db=db,startDate=startDate,endDate=endDate)
            )
        else:
            return SupportTicketsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=adminQuery.getSupportTickets(db=db,adminId=admin.id,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SupportTicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# cashout account
async def verifyCashoutAccount(
        payload:AddCashoutAccountRequest,
        response: Response,
        setting: Setting,
        admin: AdminModel,
):
        try:
            logger.info(f"Started cashout account verification process recipient {admin.firstname} {admin.lastname} for {admin.email}")
            headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
            result = util.http(f"{setting.paystack_url}bank/resolve?account_number={payload.accountNumber}&bank_code={payload.bankCode}",headers=headers)
            if result.status_code == 200:
                paystackResponse = result.json()
                if paystackResponse and paystackResponse["status"] is True:
                    recipientData = paystackResponse.get("data", {})
                    if recipientData:
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=recipientData)
                else:
                    logger.info(f"Failed to verify cashout account recipient {admin.firstname} {admin.lastname} for {admin.email}")
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
            else:
                logger.info(f"Failed to verify cashout account recipient {admin.firstname} {admin.lastname} for {admin.email}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json().get('message',"Connection problem"),)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addCashoutBankRecipient(
        payload:AddCashoutRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        admin: AdminModel,
        background_task:BackgroundTasks
):
        try:
            logger.info(f"Started adding cashout recipient {admin.firstname} {admin.lastname} for {admin.email}")
            if admin.cashout_enabled:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout account already exist",)
            else:
                headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                params ={ "type": "nuban","name":f"{admin.firstname} {admin.lastname}","account_number": payload.accountNumber,"bank_code": payload.bankCode, "currency": "NGN" }
                result = util.http(f"{setting.paystack_url}transferrecipient",params=params,headers=headers)
                if result.status_code == 201:
                    paystackResponse = result.json()
                    if paystackResponse and paystackResponse["status"] is True:
                        recipientData = paystackResponse.get("data", {})
                        if recipientData:
                            admin.cashout_enabled = True
                            admin.cashout_account = payload.accountNumber
                            admin.cashout_code = recipientData.get("recipient_code")
                            admin.cashout_bank = payload.bankCode
                            admin.updated_at = datetime.now()
                            admin.wallet.cashout_enabled = True
                            admin.wallet.cashout_account = payload.accountNumber
                            admin.wallet.cashout_code = recipientData.get("recipient_code")
                            admin.wallet.cashout_bank = payload.bankCode
                            admin.wallet.updated_at = datetime.now()
                            updatedUser = queries.create(db=db,model=admin)
                            if updatedUser:
                                background_task.add_task(notifyUser,db=db,title=f"Cashout Recipient Added", message=f"Cashout recipient {admin.firstname}{admin.lastname} added successfully",userId=admin.id, setting=setting)
                                email_debit = util.templates.TemplateResponse("cashout_setup.html",{"request": request, "user": admin,"recipient":recipientData},)
                                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Recipient Added",toAddress=admin.email)
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        logger.info(f"Failed to add cashout recipient {admin.firstname} {admin.lastname} for {admin.email}")
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                else:
                    logger.info(f"Failed to add cashout recipient {admin.firstname} {admin.lastname} for {admin.email}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json().get('message',SYSTEMBUSY),)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def cashoutLimitChange(payload:CashoutLimitRequest,response: Response,request:Request,db:Session,setting: Setting,admin: AdminModel,background_task:BackgroundTasks):
        try:
            logger.info(f"Started cashout limit change process recipient {admin.firstname} {admin.lastname} for {admin.email}")
            if int(admin.wallet.availableBalance) < int(payload.amount)*100:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Limit must be greater than purse balance",)
            latestOTP = adminQuery.getLatestOTP(db=db,adminId=admin.id,serviceName="LIMIT_CHANGE")
            if latestOTP:
                time_difference = datetime.now() - latestOTP.expired_at
                logger.info(f"Time difference since last OTP for {admin.email} is {time_difference}")
                if latestOTP.expired_at >  datetime.now():
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="An OTP has already been sent to your email. Please check your inbox.",)
            otpDigits = util.generateOTP()
            otpModel = OTPModel(
                otp=otpDigits, 
                servicename="LIMIT_CHANGE", 
                admin_id=admin.id,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=5)),
                updated_at=datetime.now(),)
            newOtp = adminQuery.create(db=db,model=otpModel)
            if newOtp:
                email_otp = util.templates.TemplateResponse("otp.html",{"request": request, "user": admin,"otp":newOtp,"service":"Cashout Limit Change"},)
                background_task.add_task(util.mailer,str(email_otp.body, "utf-8"),setting=setting,subject="OTP for Cashout Limit Change",toAddress=admin.email)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="OTP sent to your registered email",data={"otpRequired":True})
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def cashoutWithdrawal(payload:CashoutWithdrawalRequest,response: Response,request:Request,db:Session,setting: Setting,admin: AdminModel,background_task:BackgroundTasks):
        try:
            logger.info(f"Started cashout withdrawal process recipient {admin.firstname} {admin.lastname} for {admin.email}")
            if int(admin.wallet.availableBalance) < int(payload.amount)*100:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Insufficient purse balance",)
            if not admin.cashout_enabled:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout account not set up",)
            if not admin.cashout_limit:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout limit not set up",)
            if int(payload.amount)*100 > int(admin.cashout_limit):
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Amount exceeds cashout limit",)
            latestOTP = adminQuery.getLatestOTP(db=db,adminId=admin.id,serviceName="WITHDRAWAL")
            if latestOTP:
                time_difference = datetime.now() - latestOTP.expired_at
                logger.info(f"Time difference since last OTP for {admin.email} is {time_difference}")
                if latestOTP.expired_at >  datetime.now():
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="An OTP has already been sent to your email. Please check your inbox.",)
            otpDigits = util.generateOTP()
            otpModel = OTPModel(
                otp=otpDigits, 
                servicename="WITHDRAWAL", 
                admin_id=admin.id,
                created_at=datetime.now(),
                expired_at=(datetime.now() + timedelta(minutes=2)),
                updated_at=datetime.now(),)
            newOtp = adminQuery.create(db=db,model=otpModel)
            if newOtp:
                email_otp = util.templates.TemplateResponse("otp.html",{"request": request, "user": admin,"otp":newOtp,"service":"Cashout Limit Change"},)
                background_task.add_task(util.mailer,str(email_otp.body, "utf-8"),setting=setting,subject="OTP for Cashout Limit Change",toAddress=admin.email)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="OTP sent to your registered email",data={"otpRequired":True})
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def cashoutConfirmationCheck(payload:CashoutConfirmationRequest,request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,background_task:BackgroundTasks):
        try:
            logger.info(f"Started checking cashout {payload.requestType} for recipient {admin.firstname} {admin.lastname} for {admin.email}")
            latestOTP = adminQuery.getOTPValue(db=db,adminId=admin.id,serviceName=payload.requestType,otp=payload.otp)
            if latestOTP:
                if latestOTP.expired_at >  datetime.now():
                    logger.info(f"Time difference since last OTP for {admin.email} is not expired")
                    if admin.cashout_enabled:
                        if payload.requestType == "LIMIT_CHANGE":
                            admin.cashout_limit = int(payload.amount)*100
                            admin.updated_at = datetime.now()
                            admin.wallet.cashout_limit = int(payload.amount)*100
                            admin.wallet.updated_at = datetime.now()
                            latestOTP.status = OTPStatusEnum.CLOSED
                            latestOTP.updated_at = datetime.now()
                            updatedUser = adminQuery.create(db=db,model=admin)
                            if updatedUser:
                                adminQuery.create(db=db,model=latestOTP)
                                background_task.add_task(notifyUser,db=db,title=f"Cashout Limit Changed", message=f"Cashout limit changed to {payload.amount} successfully",userId=admin.id, setting=setting)
                                email_debit = util.templates.TemplateResponse("cashout_limit_change.html",{"request": request, "user": admin,"newLimit":payload.amount},)
                                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Limit Changed",toAddress=admin.email)
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Limit changed successfully",)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
                        elif payload.requestType == "WITHDRAWAL":
                            if int(payload.amount)*100 > int(admin.cashout_limit):
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Amount exceeds cashout limit",)
                            if int(admin.wallet.availableBalance) < int(payload.amount)*100:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Insufficient purse balance",)
                            cashoutPd = queries.getProductTypeBYname(db=db,name="cashout")
                            if not cashoutPd:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout product not configured",)
                            totalCashoutToday = adminQuery.totalCashoutTransactionsDaily(db=db,adminId=admin.id)
                            trnxId = f"CASH-{util.generateId()}"
                            logger.info(f"total cash out for {admin.email} today {totalCashoutToday} at {datetime.now()}")
                            newBalance = int(admin.wallet.availableBalance) - int(payload.amount)*100
                            admin.wallet.availableBalance = newBalance
                            admin.wallet.updated_at = datetime.now()
                            admin.wallet.payments.append(PaymentModel(
                                            wallet_id = admin.wallet.id,
                                            admin_id =admin.id,
                                            amount = int(payload.amount)*100,
                                            payment_type =PaymentEnum.DEBIT,
                                            reference = trnxId,
                                            event = "charge.processing",
                                            status = "processing",
                                            channel = ChannelEnum.WEB,
                                            statusCode = TransactionCodeEnum.PROCESSING,
                                            statusDescription = TransactionStatusEnum.PROCESSING,
                                            recipient=admin.cashout_account,
                                            statusMessage = f"Cashout to {admin.cashout_account} {admin.cashout_bank}",
                                            balanceBefore = admin.wallet.availableBalance,
                                            balanceAfter = newBalance,
                                            product_id=cashoutPd.product_id,
                                            product_type_id=cashoutPd.id,
                                            cashout = CashOutModel(
                                                admin_id = admin.id,
                                                source= 'balance',
                                                amount= int(payload.amount)*100,
                                                recipient= admin.cashout_account,
                                                withdrawalStatus = WithrawalStatusEnum.WAITING,
                                                statusCode = TransactionCodeEnum.PROCESSING,
                                                statusDescription = TransactionStatusEnum.PROCESSING,
                                                reference = trnxId,
                                                reason = payload.desc,
                                                created_at = datetime.now(),
                                                updated_at =  datetime.now()
                                            ),
                                            created_at =datetime.now(),
                                            updated_at = datetime.now()
                                        )
                                    )
                            updatedUser = adminQuery.create(db=db,model=admin)
                            if updatedUser:
                                latestOTP.status = OTPStatusEnum.CLOSED
                                latestOTP.updated_at = datetime.now()
                                adminQuery.create(db=db,model=latestOTP)
                                logger.info(f"Cashout withdrawal of {payload.amount} initiated successfully for {admin.email}")
                                if totalCashoutToday + int(payload.amount)*100 > int(admin.cashout_limit):
                                    background_task.add_task(notifyUser,db=db,title=f"Cashout Withdrawal Initiated", message=f"Cashout withdrawal of {payload.amount} initiated successfully",userId=admin.id, setting=setting)
                                    email_debit = util.templates.TemplateResponse("cashout_withdrawal_initiated.html",{"request": request, "user": admin,"amount":payload.amount},)
                                    background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Withdrawal Initiated",toAddress=admin.email)
                                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Cash out withdrawal initiated successfully",)
                                else:
                                    latestPayment = adminQuery.getPaymentByReference(db=db,reference=trnxId)
                                    if latestPayment and latestPayment.cashout:
                                        logger.info(f"Start processing cashout records ............... @ {datetime.now()}")
                                        headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                                        params ={"source": latestPayment.cashout.source,"amount": latestPayment.cashout.amount,"reference":latestPayment.reference,"recipient": admin.cashout_code,"reason": latestPayment.cashout.reason }
                                        result = util.http(f"{setting.paystack_url}transfer",params=params,headers=headers)
                                        if result.status_code == 200:
                                            paystackResponse = result.json()
                                            if paystackResponse and paystackResponse["status"] is True:
                                                transferData = paystackResponse.get("data", {})
                                                if transferData:
                                                    latestPayment.event = "charge.success",
                                                    latestPayment.status = "success",
                                                    latestPayment.cashout.withdrawalStatus = WithrawalStatusEnum.COMPLETED
                                                    latestPayment.cashout.statusCode = TransactionCodeEnum.SUCCESS
                                                    latestPayment.cashout.transfer_code = transferData.get("transfer_code")
                                                    latestPayment.cashout.approved = f"{admin.firstname} {admin.lastname}"
                                                    latestPayment.cashout.statusDescription = TransactionStatusEnum.SUCCESS
                                                    latestPayment.cashout.updated_at = datetime.now()
                                                    latestPayment.statusCode = TransactionCodeEnum.SUCCESS
                                                    latestPayment.statusDescription = TransactionStatusEnum.SUCCESS
                                                    latestPayment.updated_at = datetime.now()
                                                    updatedPayment = adminQuery.create(db=db,model=latestPayment)
                                                    if updatedPayment:
                                                        background_task.add_task(notifyUser,db=db,title=f"Cashout Withdrawal Successful", message=f"Cashout withdrawal of {payload.amount} completed successfully",userId=admin.id, setting=setting)
                                                        email_debit = util.templates.TemplateResponse("cashout_withdrawal_successful.html",{"request": request, "user": admin,"balance":newBalance,"amount":payload.amount},)
                                                        background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Withdrawal Successful",toAddress=admin.email)
                                                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Cash out withdrawal completed successfully",)
                                            else:
                                                logger.info(f"Failed to process cashout withdrawal for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                                        else:
                                            logger.info(f"Failed to process cashout withdrawal for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                                            response.status_code = status.HTTP_400_BAD_REQUEST
                                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json().get('message',SYSTEMBUSY),)
                                    else:
                                        logger.info(f"Failed to process cashout withdrawal for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                                        response.status_code = status.HTTP_400_BAD_REQUEST
                                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PROCESSING,)
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PROCESSING,)
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Cashout request",)
                    else:
                        logger.info(f"Failed cashout {payload.requestType} for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout Not Enabled",)
                else:
                    logger.info(f"Failed cashout {payload.requestType} for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid/Expired OTP",)
            else:
                logger.info(f"Failed cashout {payload.requestType} for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid/Expired OTP",)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def approveCashout(cashoutId: int,request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,background_task: BackgroundTasks):
    try:
        logger.info(
            f"started approval for cashout payments from {cashoutId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            cashout = adminQuery.getCashoutById(db=db,cashoutId=cashoutId)
            if cashout and cashout.withdrawalStatus == WithrawalStatusEnum.WAITING:
                logger.info(f"Start processing cashout records ............... at {datetime.now()}")
                cashoutAdmin = adminQuery.getAdmin(db=db,adminId=cashout.admin_id)
                if cashoutAdmin:
                    headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                    params ={"source":cashout.source,"amount":cashout.amount,"reference":cashout.reference,"recipient": cashoutAdmin.cashout_code,"reason": cashout.reason }
                    result = util.http(f"{setting.paystack_url}transfer",params=params,headers=headers)
                    if result.status_code == 200:
                        paystackResponse = result.json()
                        if paystackResponse and paystackResponse["status"] is True:
                            transferData = paystackResponse.get("data", {})
                            if transferData:
                                cashout.withdrawalStatus = WithrawalStatusEnum.COMPLETED
                                cashout.statusCode = TransactionCodeEnum.SUCCESS
                                cashout.approved = f"{admin.firstname} {admin.lastname}"
                                cashout.statusDescription = TransactionStatusEnum.SUCCESS
                                cashout.transfer_code = transferData.get("transfer_code")
                                cashout.updated_at = datetime.now()
                                updatedPayment = adminQuery.create(db=db,model=cashout)
                                if updatedPayment:
                                    payment = adminQuery.getPaymentByCashoutId(db=db,cashoutId=cashout.id)
                                    if payment:
                                        payment.event = "charge.success"
                                        payment.status = "success"
                                        payment.statusCode = TransactionCodeEnum.SUCCESS
                                        payment.statusDescription = TransactionStatusEnum.SUCCESS
                                        payment.updated_at = datetime.now()
                                        updatedPayment = adminQuery.create(db=db,model=payment)
                                        if updatedPayment:
                                            background_task.add_task(notifyUser,db=db,title=f"Cashout Withdrawal Successful", message=f"Cashout withdrawal of {cashout.amount} completed successfully",userId=cashoutAdmin.id, setting=setting)
                                            email_debit = util.templates.TemplateResponse("cashout_withdrawal_successful.html",{"request": request, "user": cashoutAdmin,"balance":cashoutAdmin.wallet.availableBalance,"amount":cashout.amount},)
                                            background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Withdrawal Successful",toAddress=cashoutAdmin.email)
                                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Cash out withdrawal completed successfully",)
                            else:
                                logger.info(f"Failed to process cashout withdrawal for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                        else:
                            logger.info(f"Failed to process cashout withdrawal for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                    else:
                        logger.info(f"Failed to process cashout withdrawal for recipient {admin.firstname} {admin.lastname} for {admin.email}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json().get('message',SYSTEMBUSY),)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout not eligible for rejection",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def rejectCashout(cashoutId: int,request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,background_task: BackgroundTasks):
    try:
        logger.info(
            f"started rejection for cashout payments from {cashoutId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            cashout = adminQuery.getCashoutById(db=db,cashoutId=cashoutId)
            if cashout and cashout.withdrawalStatus == WithrawalStatusEnum.WAITING:
                cashout.withdrawalStatus = WithrawalStatusEnum.REJECTED
                cashout.statusCode = TransactionCodeEnum.FAILED
                cashout.statusDescription = TransactionStatusEnum.FAILED
                cashout.updated_at = datetime.now()
                cashout.rejected = f"{admin.firstname} {admin.lastname}"
                updatedCashout = adminQuery.create(db=db,model=cashout)
                if updatedCashout:
                    payment = adminQuery.getPaymentByCashoutId(db=db,cashoutId=cashout.id)
                    if payment:
                        newBalance = int(payment.wallet.availableBalance) + int(payment.amount)
                        payment.wallet.availableBalance = newBalance
                        payment.wallet.updated_at = datetime.now()
                        payment.status = "rejected"
                        payment.statusCode = TransactionCodeEnum.FAILED
                        payment.statusDescription = TransactionStatusEnum.FAILED
                        payment.updated_at = datetime.now()
                        updatedPayment = adminQuery.create(db=db,model=payment)
                        if updatedPayment:
                            background_task.add_task(notifyUser,db=db,title=f"Cashout Withdrawal Rejected", message=f"Cashout withdrawal of {payment.amount/100} rejected successfully",userId=payment.admin_id, setting=setting)
                            return CashoutsResponse(
                                statusCode= str(status.HTTP_200_OK),
                                statusDescription="Cashout rejected successfully",
                            )
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout not eligible for rejection",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getCashoutDetail(cashoutId: int,response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(
            f"started querying cashout for ID {cashoutId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            cashout = adminQuery.getCashoutById(db=db,cashoutId=cashoutId)
            if cashout:
                cashoutAdmin = adminQuery.getAdmin(db=db,adminId=cashout.admin_id)
                if cashoutAdmin:
                    cashoutPayment = adminQuery.getPaymentByCashoutId(db=db,cashoutId=cashout.id)
                    return BaseResponse(
                        statusCode= str(status.HTTP_200_OK),
                        statusDescription=SUCCESS,
                        data={
                            "cashout":Cashout.model_validate(cashout),
                            "admin":AdminMini.model_validate(cashoutAdmin),
                            "payment":Payment.from_orm(cashoutPayment).model_dump() if cashoutPayment else None

                        })
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# admin service
async def listOfCustomer(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
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
async def getCustomerDetail(customerId: int,response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(
            f"started querying customer for ID {customerId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            customer = adminQuery.getCustomerById(db=db,customerId=customerId)
            if customer:
                return CustomerResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=customer)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def resetCustomerAccountPassword(customerId: int,request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,background_task: BackgroundTasks):
    try:
        logger.info(
            f"started reset password for {customerId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.SUPPORT,AdminRoleEnum.SUPERADMIN]:
            customer = adminQuery.getCustomerById(db=db,customerId=customerId)
            if customer:
                if customer.account_status == AccountStatusEnum.ACTIVE:
                    newPassword = util.generate_password()
                    logger.info(f"new password is {newPassword}")
                    customer.password = util.get_password_hash(newPassword)
                    customer.updated_at = datetime.now()
                    updatedCustomer = adminQuery.create(db=db,model=customer)
                    if updatedCustomer:
                        email_body = util.templates.TemplateResponse("otp.html",{"request": request, "user": customer,"otp":newPassword},)
                        background_task.add_task(
                        util.mailer,
                        str(email_body.body, "utf-8"),
                        setting=setting,
                        subject=f"Password Reset",
                        toAddress=customer.email,)
                        background_task.add_task(notifyUser,db=db,title=f"Password Reset", message=f"Your password request has been completed successfully",userId=customer.id, setting=setting)
                        return BaseResponse(statusCode= str(status.HTTP_200_OK),statusDescription="Password has been sent to customer",)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="You cannot reset password for inactive customer",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNKNOWNUSER,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def toggleCustomerAccountStatus(customerId: int,request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,background_task: BackgroundTasks):
    try:
        logger.info(
            f"started rejection for cashout payments from {cashoutId} at {datetime.now()}"
        )
        if admin.role.tag in [AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            cashout = adminQuery.getCashoutById(db=db,cashoutId=cashoutId)
            if cashout and cashout.withdrawalStatus == WithrawalStatusEnum.WAITING:
                cashout.withdrawalStatus = WithrawalStatusEnum.REJECTED
                cashout.statusCode = TransactionCodeEnum.FAILED
                cashout.statusDescription = TransactionStatusEnum.FAILED
                cashout.updated_at = datetime.now()
                cashout.rejected = f"{admin.firstname} {admin.lastname}"
                updatedCashout = adminQuery.create(db=db,model=cashout)
                if updatedCashout:
                    payment = adminQuery.getPaymentByCashoutId(db=db,cashoutId=cashout.id)
                    if payment:
                        newBalance = int(payment.wallet.availableBalance) + int(payment.amount)
                        payment.wallet.availableBalance = newBalance
                        payment.wallet.updated_at = datetime.now()
                        payment.status = "rejected"
                        payment.statusCode = TransactionCodeEnum.FAILED
                        payment.statusDescription = TransactionStatusEnum.FAILED
                        payment.updated_at = datetime.now()
                        updatedPayment = adminQuery.create(db=db,model=payment)
                        if updatedPayment:
                            background_task.add_task(notifyUser,db=db,title=f"Cashout Withdrawal Rejected", message=f"Cashout withdrawal of {payment.amount/100} rejected successfully",userId=payment.admin_id, setting=setting)
                            return CashoutsResponse(
                                statusCode= str(status.HTTP_200_OK),
                                statusDescription="Cashout rejected successfully",
                            )
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout not eligible for rejection",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
