
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
from fastapi import Depends,Header,status
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from schemas.request import TransactionPINRequest

logger = logging.getLogger(__name__)
# initialise fast api instance
middlewares = [
    Middleware(TrustedHostMiddleware, allowed_hosts=["*"]#util.get_setting().allowed_hosts
               ),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],#util.get_setting().allowed_origins,
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
        logger.info(payload)
        user = authQuery.userByEmailOrPhone(
            db=db,
            email=payload["username"],
            phonenumber=payload["username"],
        )
        logger.info(user)
        if user is None:
            raise credentials_exception
        return Customer.model_validate(user)
    except JWTError:
        raise credentials_exception
async def validateTransactionPIN(
    payload:TransactionPINRequest,
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
        logger.info(payload)
        decodedToken = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        user = authQuery.userByEmailOrPhone(
            db=db,
            email=decodedToken["username"],
            phonenumber=decodedToken["username"],
        )
        if user is None:
            raise credentials_exception
        validatedUser = Customer.model_validate(user)
        if validatedUser.account_status == AccountStatusEnum.ACTIVE.value:
            logger.info(payload.pin)
            if util.verify_password(payload.pin, user.pin) is True:
                return validatedUser
            raise util.UnicornException(
                status=status.HTTP_403_FORBIDDEN,
                error={
                    "statusCode": str(status.HTTP_403_FORBIDDEN),
                    "statusDescription":INVALIDPIN,
                },
            )
        else:
            raise util.UnicornException(
                status=status.HTTP_403_FORBIDDEN,
                error={
                    "statusCode": str(status.HTTP_403_FORBIDDEN),
                    "statusDescription": f"Your account is {validatedUser.account_status}",
                },
            )
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
async def validateDevice(
    device: Annotated[str, Header()],
):
    try:
        logger.info(device)
        validatedDevice = Device.model_validate(json.loads(device))
        if validatedDevice:
            if validatedDevice.isPhysicalDevice is True:
                return validatedDevice
            raise device_exception
        raise device_exception
    except Exception as ex:
        logger.info(ex)
        raise device_exception
async def validateAdmin(
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
        user = adminQuery.admin(
            db=db,
            username=payload["username"],
        )
        if user:
            logger.info(user.status)
            if user.status:
                logger.info(user.status)
                return Admin.from_orm(user)
            raise util.UnicornException(
                status=status.HTTP_401_UNAUTHORIZED,
                error={
                    "statusCode": str(status.HTTP_401_UNAUTHORIZED),
                    "statusDescription": f"Your account is {user.status.value}",
                },
            )
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


