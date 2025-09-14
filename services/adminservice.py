
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import authQuery,queries,adminQuery
from datetime import datetime,timedelta
from schemas import otp
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.role import *
from schemas.product import *
from schemas.product_type import *
from schemas.admin import *
from schemas.station import *
from schemas.seat import *
from schemas.schedule import *
from schemas.route import RoutesResponse,AddRouteRequest
from schemas.ticket import TicketsResponse
from schemas.bus import BusesResponse,AddBusRequest
from schemas.park import ParksResponse
from schemas.train import *
from schemas.notification import NotificationsResponse
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
        payload: CreateAdminRequest,
        background_task: BackgroundTasks,):
    try:
        if payload.id:
            logger.info(f"updating user {payload.firstname} at {str(datetime.now())}")
        else:
            logger.info(f"creating new user {payload.firstname} at {str(datetime.now())}")
            user = authQuery.getCheckAdmin(db=db,username=payload.email)
            if user:
                response.status_code = status.HTTP_302_FOUND
                return BaseResponse(statusCode=str(status.HTTP_302_FOUND),statusDescription=ALREADYEXIST,)
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
                        "user":Admin.from_orm(user),
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
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            password = util.generateOTP()
            logger.info(f"New admin created {payload.firstname} with password {password}")
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
                    wallet=AccountModel(walletAccount=util.formatPhoneShort(payload.phonenumber),availableBalance=0,created_at=datetime.now(),updated_at=datetime.now())
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
def updateAccount(db: Session,setting: Setting,payload: CreateAdminRequest, background_task: BackgroundTasks, request: Request,response: Response):
    try:
        logger.info("started creating new admin account")
        role = adminQuery.getRole(db=db,roleId=payload.tag)
        if role:
            password = util.generateOTP
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
                existing = adminQuery.getRoleByTag(db=db,tag=AdminRoleEnum(role))
                if existing:
                    return AdminsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getAllAdminByRole(db=db,roleId=existing.id))
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
            new = RoleModel(name=payload.name,tag=AdminRoleEnum(payload.tag),status=payload.status,description=payload.description,created_at=datetime.now(),updated_at=datetime.now(),)
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
        if admin.role.tag in[AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
            adminId = admin.id if admin.role.tag in [AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER] else None
            routes = adminQuery.getRoutesByIds(db=db,ids=payload.busroutes,adminId=adminId)
            if routes:
                schedules =  adminQuery.getSchedulesByIds(db=db,ids=payload.busschedules,adminId=None)
                if schedules:
                    previous = adminQuery.getBus(db=db,busNumber=payload.bus_number)
                    if previous and previous.admin_id == admin.id:
                        previous.airCondition = payload.airCondition
                        previous.tv = payload.tv
                        previous.base_price = payload.base_price
                        previous.camera = payload.camera
                        previous.name = payload.name
                        previous.seatCount = payload.seatCount
                        previous.description = payload.description
                        previous.schedules = schedules
                        previous.routes = routes
                        previous.updated_at = datetime.now()
                    else:
                        previous = BusModel(admin_id=admin.id,seatCount=payload.seatCount,name=payload.name,bus_number=payload.bus_number,description=payload.description,tv=payload.tv,camera=payload.camera,airCondition=payload.airCondition,base_price=payload.base_price,created_at=datetime.now(),updated_at=datetime.now(),schedules=schedules,routes=routes)
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
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOSCHEDULE)
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
async def updateBus(db: Session,setting: Setting,payload: AddBusRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
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
async def deleteBus(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,busId: int):
    try:
        logger.info(f"started deleting bus {busId} @ {datetime.now()}")
        role = queries.deleteBus(db=db,busId=busId)
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
        logger.info(f"started creating new admin role @ {datetime.now()}")
        if admin.role.tag in[AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER,AdminRoleEnum.ADMIN,AdminRoleEnum.SUPERADMIN]:
            adminId = admin.id if admin.role.tag in [AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER] else payload.admin_id
            routes = adminQuery.getRoutesByIds(db=db,ids=payload.routes,adminId=adminId)
            if routes:
                schedules =  adminQuery.getSchedulesByIds(db=db,ids=payload.schedules,adminId=None)
                if schedules:
                    seatsClass = adminQuery.getSeatsByIds(db=db,ids=payload.seats,adminId=adminId)
                    if seatsClass:
                        previous = adminQuery.getTrain(db=db,trainNumber=payload.trainNumber)
                        if previous and previous.admin_id == adminId:
                            previous.trainName = payload.trainName
                            previous.seats = seatsClass
                            previous.description = payload.description
                            previous.schedules = schedules
                            previous.routes = routes
                            previous.updated_at = datetime.now()
                        else:
                            previous = TrainModel(admin_id=admin.id,trainNumber=payload.trainNumber,trainName=payload.trainName,description=payload.description,created_at=datetime.now(),updated_at=datetime.now(),schedules=schedules,routes=routes,seats=seatsClass)
                        created = queries.create(db=db, model=previous)
                        if created:
                            email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOSEAT)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOSCHEDULE)
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
async def updateTrain(db: Session,setting: Setting,payload: AddRoleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
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
async def deleteTrain(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,roleId: int):
    try:
        logger.info(f"started deleting role {roleId} @ {datetime.now()}")
        role = queries.deleteRole(db=db,roleId=roleId)
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
            existing = adminQuery.getRouteByStartStopStation(db=db,start=payload.startId, stop=payload.stopId,adminId=admin.id)
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
                        previous = adminQuery.getRouteById(db=db,routeId=payload.id)
                        if previous and previous.admin_id == admin.id:
                            #previous.buses = busess
                            previous.destinationStation_id=stopStation.id
                            previous.sourceStation_id=startStation.id
                            previous.updated_at = datetime.now()
                        else:
                            previous = RouteModel(routeName=payload.routeName,sourceStation_id=startStation.id,destinationStation_id=stopStation.id,mode=startStation.mode,admin_id=admin.id,created_at=datetime.now(),updated_at=datetime.now())
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
async def updateRoute(db: Session,setting: Setting,payload: AddRoleRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
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
async def deleteRoute(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,routeId: int):
    try:
        logger.info(f"started deleting route {routeId} @ {datetime.now()}")
        role = queries.deleteRoute(db=db,routeId=routeId)
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
                if payload.id:
                    existing = queries.getStationById(db=db,stationId=payload.id)
                    if existing:
                        existing.stationName = payload.stationName
                        existing.location = payload.location
                else:
                    existing = StationModel(
                                    admin_id = admin.id,
                                    stationName = payload.stationName,
                                    location =  payload.location,
                                    description = f"{payload.stationName} {payload.location}",
                                    parkImage = payload.location,
                                    address = f"{payload.stationName} {payload.location}",
                                    contact = admin.phonenumber,
                                    policy = "",
                                    status = True,
                                    mode= TicketModeEnum(payload.mode) )
                created = queries.create(db=db,model=existing)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Role",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
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
async def deleteStation(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,roleId: int):
    try:
        logger.info(f"started deleting station {roleId} @ {datetime.now()}")
        role = queries.deleteStation(db=db,stationId=roleId)
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
