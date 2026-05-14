from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Query,Form,UploadFile,
    Request,File,
    BackgroundTasks,
)
from schemas.bus_type import BusTypesResponse
from schemas.response import *
from schemas.request import *
from sqlalchemy.orm import Session
from utils.constant import *
from utils import util
from typing import Annotated
from utils.dependencies import (
    getSystemSetting,validateAdmin,
)
from utils.database import get_db
from services import adminservice,glAccountingService,productservice,paymentservice
from schemas.customer import *
from schemas.admin import *
from schemas.cashout import *
from schemas.role import *
from schemas.station import *
from schemas.route import RoutesResponse,AddRouteRequest
from schemas.bus_route import BusRoutesResponse,AddBusRouteRequest
from schemas.bus_schedule import BusSchedulesResponse,AddBusScheduleRequest
from schemas.train import *
from schemas.bus import BusesResponse,AddBusRequest
from schemas.park import ParksResponse
from schemas.ticket import TicketsResponse,TicketResponse
from schemas.notification import NotificationsResponse
from schemas.schedule import *
from schemas.commission import *
from schemas.service_rate import *
from schemas.general_ledger import *
from schemas.journal import *
from schemas.product import *
from schemas.bus_type import *
from schemas.product_type import *
from schemas.package import *
from schemas.payment import *
from schemas.transaction import *
from schemas.gl_posting_rules import *
from models.model import *
from datetime import date
from schemas.setting import Setting
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/gl-account")
async def create_gl_account(
    payload: dict,
    db: Session = Depends(get_db)
):

    account = GLAccountModel(
        code=payload["code"],
        name=payload["name"],
        gl_type=payload["gl_type"],
        party_type=payload.get("party_type"),
    )

    db.add(account)
    db.commit()

    return {
        "status": True,
        "message": "GL Account created"
    }
@router.get("/gl-account")
async def list_gl_accounts(
    db: Session = Depends(get_db)
):

    accounts = db.query(GLAccountModel).all()

    return accounts
@router.post("/posting-rule/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True)
async def create_posting_rule(
    payload:AddPostingRuleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        return await glAccountingService.addPostingRules(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/posting-rules",
    response_model=PostingRulessResponse,
    response_model_exclude_unset=True,)
async def list_posting_rules(response: Response,admin: Annotated[AdminModel, Depends(validateAdmin)],db: Annotated[Session, Depends(get_db)]):
    try:
        return await glAccountingService.listOfPostingRules(db=db,response=response,admin=admin )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)