
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import authQuery,queries,adminQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.role import *
from schemas.admin import *
from schemas.general_ledger import *
from schemas.service_rate import *
from schemas.commission import *
from schemas.route import RoutesResponse,AddRouteRequest
from schemas.ticket import TicketsResponse
from schemas.bus import BusesResponse,AddBusRequest
from schemas.park import ParksResponse
from schemas.train import TrainsResponse
from schemas.notification import NotificationsResponse
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)

# ledger
async def listOfLedgers(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying ledger..............@ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            return GLedgersResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getGlAccounts(db=db))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return GLedgersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return GLedgersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addLedger(db: Session,setting: Setting,payload: AddGLRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new ledger @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            if payload.id:
                logger.info(f"started updating ledger {payload.id} @ {datetime.now()}")
                existing = adminQuery.getGlAccountById(db=db,id=payload.id)
                if existing:
                    existing.name = payload.name
                    existing.gl_type = payload.gl_type
                    existing.updated_at = datetime.now()
                    created = queries.create(db=db,model=existing)
                    if created:
                        email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                        background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Ledger",toAddress=admin.email,)
                        return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
            else:
                glcode = f"GL{util.generateId()}"
                new = GLAccountModel(name=payload.name,code=glcode,gl_type=AccountType(payload.gl_type),created_at=datetime.now(),updated_at=datetime.now(),)
                created = queries.create(db=db,model=new)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Ledger",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteLedger(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,id: int):
    try:
        logger.info(f"started deleting GlAccount {id} @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            existing = adminQuery.deleteGlAccount(db=db,id=id)
            if existing:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# ledger
async def listOfCommissions(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying ledger..............@ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            return CommissionsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getServiceCommissions(db=db))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addCommission(db: Session,setting: Setting,payload: AddCommissionRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new ledger @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            if payload.id:
                logger.info(f"started updating ledger {payload.id} @ {datetime.now()}")
                existing = adminQuery.getServiceCommissionById(db=db,id=payload.id)
                if existing:
                    existing.commission_rate = payload.commission_rate
                    existing.commission_type = payload.commission_type
                    existing.updated_at = datetime.now()
                    created = adminQuery.create(db=db,model=existing)
                    if created:
                        email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                        background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Update on Service Commission",toAddress=admin.email,)
                        return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
            else:
                new = CommissionModel(product_type_id=payload.product_type_id,admin_id=payload.admin_id,commission_type=payload.commission_type,commission_rate=payload.commission_rate,created_at=datetime.now(),updated_at=datetime.now(),)
                created = adminQuery.create(db=db,model=new)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Service commission",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteCommission(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,id: int):
    try:
        logger.info(f"started deleting Commission {id} @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            existing = adminQuery.deleteServiceCommission(db=db,id=id)
            if existing:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# ledger
async def listOfDiscounts(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying ledger..............@ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.BUSINESS]:
            return ProvidersResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getServiceProviders(db=db))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addDiscount(db: Session,setting: Setting,payload: AddProviderRateRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new ledger @ {datetime.now()}")
        if payload.id:
            logger.info(f"started updating ledger {payload.id} @ {datetime.now()}")
            existing = adminQuery.getServiceProviderById(db=db,id=payload.id)
            if existing:
                existing.provider_discount_rate = payload.provider_discount_rate
                existing.provider_discount_type = payload.provider_discount_type
                existing.active = payload.active
                existing.updated_at = datetime.now()
                created = adminQuery.create(db=db,model=existing)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Service Discount Update",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        else:
            new = ServiceRateModel(admin_id=payload.admin_id,product_type_id=payload.product_type_id,provider_discount_type=payload.provider_discount_type,provider_discount_rate=payload.provider_discount_rate,active=payload.active,created_at=datetime.now(),updated_at=datetime.now(),)
            created = queries.create(db=db,model=new)
            if created:
                email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Service Discount",toAddress=admin.email,)
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteDiscount(db: Session,response: Response,admin:AdminModel,id: int):
    try:
        logger.info(f"started deleting Discount {id} @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            existing = adminQuery.deleteServiceProvider(db=db,id=id)
            if existing:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
