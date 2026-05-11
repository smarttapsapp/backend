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
from schemas.support_ticket import *
from schemas.seat import *
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
@router.post("/posting-rule")
async def create_posting_rule(
    payload: dict,
    db: Session = Depends(get_db)
):

    rule = GLPostingRule(
        transaction_type=payload["transaction_type"],
        entry_type=payload["entry_type"],
        account_role=payload["account_role"],
        account_code=payload["account_code"],
    )

    db.add(rule)

    db.commit()

    return {
        "status": True,
        "message": "Posting rule created"
    }
@router.get("/posting-rule")
async def list_posting_rules(
    db: Session = Depends(get_db)
):

    rules = db.query(GLPostingRule).all()

    return rules