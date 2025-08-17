
import json
import logging
from utils import util
from models.model import AccountStatusEnum
from models.queries import settingQuery,adminQuery,authQuery
from schemas.setting import Setting
from utils.constant import *
from typing import Annotated
from schemas.customer import Customer
from schemas.admin import Admin
from jose import jwt, JWTError
from schemas.device import Device
from utils.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends,Header,status,Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from schemas.request import PINRequest

logger = logging.getLogger(__name__)
# initialise fast api instance
middlewares = [
    Middleware(TrustedHostMiddleware, allowed_hosts=util.get_setting().allowed_hosts
               ),
    Middleware(
        CORSMiddleware,
        allow_origins=util.get_setting().allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
]
device_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": str(status.HTTP_401_UNAUTHORIZED), "statusDescription": UNSUPPORTEDDEVICE},
    )
def getSystemSetting(db: Session = Depends(get_db)):
    settings = settingQuery.setting(db=db)    
    if settings:
        logger.info(settings.app_name)
        return Setting.model_validate(settings)
    logger.info("Unable to get system setting. please check database settings for more info")
    exit(code=99)
async def validateDevice(
    device: Annotated[str, Header()],
) -> Device:
    try:
        logger.info(device)
        parsed = json.loads(device)
        validated_device = Device(**parsed)
        if not validated_device.isPhysicalDevice:
            raise device_exception
        return validated_device
    except Exception as ex:
        logger.info(ex)
        raise device_exception
async def validateRegistration(
    token: str = Depends(util.oauth2_scheme),
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    credentials_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Your session has expired!"},
    )
    try:
        payload = jwt.decode(
            token, setting.secret_key, algorithms=[setting.algorithm]
        )
        logger.info(payload)
        user = authQuery.userByEmailOrPhone(
            db=db,
            email=payload["username"],
            phonenumber=payload["username"],
        )
        logger.info(user)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
async def verified_user(
    device: Annotated[Device, Depends(validateDevice)],
    token: str = Depends(util.oauth2_scheme),
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        logger.info(payload)
        user = authQuery.userByEmailOrPhone(db=db,email=payload["username"],phonenumber=payload["username"],)
        logger.info(user.account_status)
        if user is None:
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode":str(status.HTTP_404_NOT_FOUND), "statusDescription": UNKNOWNUSER},)
        if user.device and user.device.imeiNo != device.imeiNo:
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription": DEVICEMISMATCH,},)
        if user.account_status != AccountStatusEnum.REG and user.account_status != AccountStatusEnum.ACTIVE:
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription": "Inactive account",},)
        return user
    except JWTError:
        raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": "401", "statusDescription": "Your session has expired!"},)
async def validateTransactionPIN(
    payload:PINRequest,
    device: Annotated[Device, Depends(validateDevice)],
    token: str = Depends(util.oauth2_scheme),
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    try:
        auth = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        logger.info(payload)
        user = authQuery.userByEmailOrPhone(db=db,email=auth["username"],phonenumber=auth["username"],)
        if user is None:
            raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode":str(status.HTTP_404_NOT_FOUND), "statusDescription": UNKNOWNUSER},)
        if user.device.imeiNo != device.imeiNo:
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription": DEVICEMISMATCH,},)
        print(user.account_status)
        if user.account_status != AccountStatusEnum.ACTIVE:
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription": "Inactive account",},)
        if not util.verify_password(payload.pin, user.pin):
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription": INVALIDPIN,},)
        #selectedWallet = next((acct for acct in user.wallets if acct.nuban == payload.senderAccount), None)
        #if selectedWallet is None:
        #    raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode":str(status.HTTP_404_NOT_FOUND), "statusDescription": INVALIDACCOUNT},)
        #if int(payload.amount) > int(user.wallet.availableBalance):
        #    raise util.UnicornException(status=status.HTTP_400_BAD_REQUEST,error={"statusCode": str(status.HTTP_400_BAD_REQUEST),"statusDescription": INSUFFICIENTFUND,},)
        return user
    except JWTError:
        raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": "401", "statusDescription": "Your session has expired!"},)
    
async def validateCustomer(
    request: Request,
    token: str = Depends(util.oauth2_scheme),
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    credentials_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Your session has expired!"},
    )
    try:
        if token:
            payload = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
            logger.info(payload)
            customer = authQuery.userByEmailOrPhone(db=db,email=payload["username"],phonenumber=payload["username"],)
            if customer:
                print(request)
                if customer.account_status == AccountStatusEnum.ACTIVE:
                    return customer
                raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription": f"Your account is {customer.account_status}",},)
            raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription":UNKNOWNUSER,},)
        raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_401_UNAUTHORIZED),"statusDescription":"Your session has expired!",},)
    except JWTError:
        raise credentials_exception
async def get_device_header(device: Annotated[str, Header()]):
    try:
        logger.info(device)
        return Device.model_validate(json.loads(device))
    except Exception as ex:
        print(ex)
        raise util.UnicornException(
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error={
                "statusCode": str(status.HTTP_422_UNPROCESSABLE_ENTITY),
                "statusDescription": "invalid header parameter",
            },
        )
async def validateAdmin(
        request:Request,
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    credentials_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Your session has expired!"},
    )
    try:
        token = request.cookies.get("access_token")
        logger.info(token)
        if token:
            payload = jwt.decode(
            token, setting.secret_key, algorithms=[setting.algorithm]
        )
            logger.info(payload)
            user = adminQuery.admin(
            db=db,
            username=payload["username"],
        )
            if user:
                logger.info(user.status)
                if user.status:
                    logger.info(user.status)
                    return user
                raise util.UnicornException(
                status=status.HTTP_401_UNAUTHORIZED,
                error={
                    "statusCode": str(status.HTTP_401_UNAUTHORIZED),
                    "statusDescription": f"Your account is {user.status.value}",
                },)
            raise credentials_exception
        raise credentials_exception
    except JWTError:
        raise credentials_exception
async def get_current_user(
    #device: Annotated[Device, Depends(validateDevice)],
    token: str = Depends(util.oauth2_scheme),
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    credentials_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Your session has expired!"},
    )
    try:
        payload = jwt.decode(
            token, setting.secret_key, algorithms=[setting.algorithm]
        )
        user = crud.get_user_phone(
            db=db,
            phonenumber=payload["username"],
        )
        if user is None:
            raise credentials_exception
        validatedUser = Customer.model_validate(user)
        if validatedUser.account_status == AccountStatusEnum.ACTIVE.value:
            return validatedUser
        else:
            raise util.UnicornException(
                status=status.HTTP_401_UNAUTHORIZED,
                error={
                    "statusCode": str(status.HTTP_401_UNAUTHORIZED),
                    "statusDescription": f"Your account is {validatedUser.account_status}",
                },
            )
    except JWTError:
        raise credentials_exception


