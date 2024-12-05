
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import paymentQuery,authQuery
from datetime import datetime,timedelta
from schemas import otp
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

def fundViaPaystack(
        user:Customer,
        request: Request,
        db: Session,
        response: Response,
        setting: Setting,amount:str):
    try:
        payment = PaymentModel(
            wallet_id = user.wallet.id,
            user_id = user.id,
            amount = amount,
            payment_type = PaymentEnum.CREDIT,
            created_at = datetime.now(),
            updated_at= datetime.now(),
        )
        createdPayment = paymentQuery.create_payment(db=db,payment=payment)
        appResponse = None
        if createdPayment:
            headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
            params = {"email": user.email,"amount": amount}
            result = util.httpV2(setting.paystack_url,params=params,headers=headers)
            logger.info(result)
            if result.status_code == 200:
                paystackResponse = result.json()
                if paystackResponse and paystackResponse["status"] is True:
                    createdPayment.reference = paystackResponse["data"]["reference"]
                    createdPayment.access_code = paystackResponse["data"]["access_code"]
                    createdPayment.statusCode = str(status.HTTP_200_OK)
                    createdPayment.statusMessage = paystackResponse["message"]
                    appResponse = BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=paystackResponse["message"],data=paystackResponse["data"])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    createdPayment.statusCode = str(status.HTTP_400_BAD_REQUEST)
                    createdPayment.statusMessage = paystackResponse["message"]
                    appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse["message"])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                createdPayment.statusCode = str(status.HTTP_400_BAD_REQUEST)
                createdPayment.statusMessage = "Failed"
                appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
            createdPayment.event = "initialize"
            updatePayment = paymentQuery.create_payment(db=db,payment=createdPayment)
            if updatePayment:
                return appResponse
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
        else:
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def fundNotificationViaPaystack(
    request: Request,
    db: Session,
    setting: Setting,
    response: Response,
    background_task: BackgroundTasks,):
    try:
        json_data = await request.json()
        logger.info(f"incoming payment from paystack {str(json_data)}")
        payment = paymentQuery.getPaymentByReference(db=db,reference=json_data["data"]["reference"])
        if payment:
            payment.event = json_data["event"]
            payment.channel = json_data["data"]["channel"]
            payment.payment_date = json_data["data"]["channel"]
            payment.status = json_data["data"]["status"]
            payment.fee = json_data["data"]["fees"]
            payment.paystack_id = json_data["data"]["id"]
            payment.payment_date = json_data["data"]["paid_at"]
            payment.balanceBefore = payment.wallet.availableBalance
            payment.balanceAfter = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
            payment.wallet.availableBalance = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
            payment.updated_at = datetime.now()
            payment.user.hasAuthToken = True
            updatedPayment = paymentQuery.create_payment(db=db,payment=payment)
            if updatedPayment:
                card = paymentQuery.getCardByLast4(db=db,last4=json_data["authorization"]["last4"])
                if card is None:
                    createCard = CardsModel(
                        user_id= payment.user_id,
                        authorization_code=json_data["authorization"]["authorization_code"],
                        bin=json_data["authorization"]["bin"],
                        last4=json_data["authorization"]["last4"],
                        exp_month=json_data["authorization"]["exp_month"],
                        exp_year=json_data["authorization"]["exp_year"],
                        channel=json_data["authorization"]["channel"],
                        card_type=json_data["authorization"]["card_type"],
                        bank=json_data["authorization"]["bank"],
                        signature=json_data["authorization"]["signature"],
                        account_name=json_data["authorization"]["account_name"],
                        reusable=json_data["authorization"]["reusable"],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    addCard = paymentQuery.create_card(db=db,card=createCard)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to add fund",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def createAccount(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        payload: CustomerRequest,
        background_task: BackgroundTasks,):
    try:
        user = authQuery.getCheckAdmin(db=db,username=payload.email)
        if user:
            response.status_code = status.HTTP_302_FOUND
            return BaseResponse(
                    statusCode=str(status.HTTP_302_FOUND),
                    statusDescription=ALREADYEXIST,
                )
        else:
            return createUserAccount(db=db,setting=setting,payload=payload,background_task=background_task,request=request,response=response)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription=SYSTEMBUSY,
                )
def authenticate_user(
        db: Session,
    response: Response,
    setting: Setting,
    background_task: BackgroundTasks, payload: LoginRequest):
    user = authQuery.getCheckAdmin(username=payload.username, db=db)
    if user:
        if util.verify_password(payload.password, user.password) is True:
            if user.status:
                authToken = util.create_access_token(setting=setting,credentials={"username": user.email,"password": payload.password,},exp=600)
                logger.info(authToken)
                return BaseResponse(
                    statusCode= str(status.HTTP_200_OK),
                    statusDescription= f"Login Successful",
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
async def resetPasswordInitiate(
    request: Request,
    user: Customer,
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
                return BaseResponse(
                                        statusCode=str(status.HTTP_200_OK),
                                        statusDescription=f"Account already created",
                                    )
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                    statusDescription="User OTP failed or expired",
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
def createUserAccount(db: Session,setting: Setting,payload: CustomerRequest, background_task: BackgroundTasks, request: Request,response: Response):
    try:
        logger.info("started getting bvn records from bvn provider")
        password = util.generateOTP()
        user = AdminModel(
            firstname=payload.firstname,
            lastname=payload.lastname,
            email=payload.email,
            phonenumber=payload.phonenumber,
            status=payload.status,
            role=payload.role,
            password=util.get_password_hash(password),
            businesscode=payload.code
            )
        createdAccount = authQuery.create_account(db=db, user=user)
        if createdAccount:
            email_body = util.templates.TemplateResponse(
                    "onboarding.html",
                    {"request": request, "user": user,"password":password},
                )
            background_task.add_task(
                    util.mailer,
                    str(email_body.body, "utf-8"),
                    setting=setting,
                    subject="Onboarding Notification",
                    toAddress=user.email,
                )
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
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
def resetPasswordFinal(db:Session,response:Response,token:str,setting: Setting, background_task: BackgroundTasks,payload:ResetPasswordRequest):
    try:
        data = util.jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        if data:
            logger.info(data)
            user = get_user_phone(db=db,phonenumber=data["username"])
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
