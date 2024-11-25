from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.response import *
from schemas.request import *
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import (
    getSystemSetting,validateAdmin,
)
from utils import util
from utils.database import get_db
from services import configurationservice
from schemas.setting import Setting,SettingsResponse,SettingResponse
from schemas.admin import Admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["configuration"])


#API setting 
@router.get("/api", 
    response_model=SettingResponse,
    response_model_exclude_unset=True,name="get dashboard Analytics")
async def getSettingRequest(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return configurationservice.getAPIsetting(
                db=db,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SettingResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )









