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

# admin
@router.post(
    "/login",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.authenticateUser(
            request=request,
            response=response,
            setting=setting,
            db=db,
            background_task=background_task,
            payload=payload,
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post("/logout", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="user balance")
async def postLogout(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            logger.info(request.cookies.get("access_token"))
            logger.info(f"{admin.id} logged out")
            response.delete_cookie("access_token",path="/",
                    httponly=True, 
                    samesite="None",)
            return BaseResponse(
            statusCode=str(status.HTTP_200_OK),
            statusDescription=SUCCESS,
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get("/profile", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="user profile")
async def getAdminProfile(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.profile(
                db=db,request=request,response=response,setting=setting,admin=admin
            )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=INVALIDACCOUNT,
        )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
@router.post(
    "/add",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Open account on Better",
)
async def createAdmin(
    request: Request,
    payload: CreateAdminRequest,
    responses: Response,
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        userRequest = CreateAdminRequest.model_validate(payload)
        logger.info(userRequest.model_dump_json())
        return await adminservice.createAccount(request=request,response=responses,setting=Setting,db=db,payload=payload,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get("/users", 
    response_model=AdminsResponse,
    response_model_exclude_unset=True,name="get all user")
async def getAdmins(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    role: str = Query(None),
):
    try:
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPPORT,AdminRoleEnum.ADMIN]:
            if role:
                return await adminservice.listOfAdminsByRole(response=response,db=db,admin=admin,role=role) 
            else: 
                return await adminservice.listOfAdmins(db=db,response=response,admin=admin,)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return BaseResponse(statusCode=str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/bus-providers",response_model=AdminsResponse,response_model_exclude_unset=True)
async def get_bus_providers(response: Response,admin: Annotated[AdminModel, Depends(validateAdmin)],db: Annotated[Session, Depends(get_db)]):
    try:
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPPORT,AdminRoleEnum.ADMIN]:
            return await adminservice.listOfBusProviders(db=db,response=response,admin=admin,)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return BaseResponse(statusCode=str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/train-providers",response_model=AdminsResponse,response_model_exclude_unset=True)
async def get_train_providers(response: Response,admin: Annotated[AdminModel, Depends(validateAdmin)],db: Annotated[Session, Depends(get_db)]):
    try:
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPPORT,AdminRoleEnum.ADMIN]:
            return await adminservice.listOfTrainProviders(db=db,response=response,admin=admin,)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return BaseResponse(statusCode=str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/change-password",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["customer"])
async def change_admin_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.changeAdminPassword(
                request=request,
                db=db,
                response=response,
                admin=admin,
                setting=Setting,
                payload=payload,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/photo/update",response_model=BaseResponse,response_model_exclude_unset=True,)
async def upload_profile_image(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    img: UploadFile = File(...),
):
    try:
        return await adminservice.uploadProfileImage(response=response,db=db,admin=admin,setting=Setting,request=request,background_task=background_task,img=img)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )

# roles
@router.get("/roles", 
    response_model=RolesResponse,
    response_model_exclude_unset=True,tags=["role"])
async def getRoles(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.listOfRoles(
                db=db,
                setting=Setting,
                request=request,
                response=response,
                admin=admin,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RolesResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/role/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["role"])
async def addRole(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/role/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["role"])
async def updateRole(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/role/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["role"])
async def addRole(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteRole(
            roleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )

#dashboard 
@router.get("/dashboard", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get dashboard Analytics")
async def getDashboardRequest(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.analytics(
                db=db,
                setting=Setting,
                request=request,
                response=response,
                admin=admin,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
#dashboard 
@router.get("/dashboard_product", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,name="get dashboard Analytics")
async def getDashboardProductRequest(
    request: Request,
    response: Response,
    user: Annotated[AdminModel, Depends(validateAdmin)],
    Setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await  adminservice.getDashboardByProducts(
                db=db,
                setting=Setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# bus type
@router.get("/bus-types", 
    response_model=BusTypesResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def bus_types(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BusTypesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await  adminservice.listOfBusTypes(response=response,db=db,admin=admin)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusTypesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/bus-type/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def addBusType(
    payload:AddBusTypeRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addBusType(db=db,setting=setting,payload=payload,request=request,response=response,admin=admin,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/bus-type/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def deleteBusType(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteBusType(
            id=id,
                db=db,
                request=request,
                response=response,
                setting=setting,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )


# station
@router.get("/bus/stations", 
    response_model=StationsResponse,
    response_model_exclude_unset=True,tags=["station"])
async def get_bus_stations(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfStations(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,mode=MovableEnum('bus'))

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/train/stations", 
    response_model=StationsResponse,
    response_model_exclude_unset=True,tags=["station"])
async def get_train_stations(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfStations(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,mode=MovableEnum('train'))

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/station/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["station"])
async def addStation(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    parkImage: UploadFile= File(None),
    id: Optional[int] = Form(None),
    admin_id: int = Form(...),
    stationName: str = Form(...),
    location: str = Form(...),
    description: Optional[str] = Form(None),
    address: Optional[str] = Form(False),
    camera: Optional[bool] = Form(False),
    status: Optional[bool] = Form(False),
    contact: str = Form(...),
    mode: str = Form(...),
):
    try:
        payload=AddStationRequest(
            id=id,
            stationName=stationName,
            mode=mode,
            admin_id=admin_id,
            location=location,
            address=address,
            camera=camera,
            status=status,
            contact=contact,description=description)
        return await adminservice.addStation(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task,
                parkImage=parkImage
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/station/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["station"])
async def updateStation(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/station/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["station"])
async def deleteStation(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteStation(
            stationId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                setting=setting,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
#routes
@router.get("/routes", 
    response_model=RoutesResponse,
    response_model_exclude_unset=True,tags=["route"])
async def get_routes(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfRoutes(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/routes/{providerId}", 
    response_model=BusRoutesResponse,
    response_model_exclude_unset=True,tags=["route"])
async def get_routes_via_provider(
    providerId:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT,AdminRoleEnum.BUSPROVIDER]:
            return await  adminservice.listOfAdminRoutes(response=response,db=db,providerId=providerId)
        return BusRoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusRoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/route/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["route"])
async def addRoute(
    payload:AddRouteRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if payload.identifier:
            return await adminservice.updateRoute(payload=payload,db=db,setting=setting,request=request,response=response,admin=admin,background_task=background_task)
        return await adminservice.addRoute(payload=payload,db=db,setting=setting,request=request,response=response,admin=admin,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/route/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["route"])
async def updateRoute(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/route/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["route"])
async def deleteRoute(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteRoute(
            routeId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                setting=setting,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
#schedules
@router.get("/bus-schedules", 
    response_model=BusSchedulesResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def get_bus_schedules(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.listOfBusSchedules(
                response=response,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusSchedulesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/bus-schedule/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def add_bus_schedule(
    payload:AddBusScheduleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addBusSchedule(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/bus-schedule/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def delete_bus_schedule(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteSchedule(
            scheduleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY, )
@router.get("/bus-manifest/{tripId}",response_model=TicketsResponse,response_model_exclude_unset=True,tags=["route"])
async def get_trip_manifest(tripId:int,response: Response,admin: Annotated[AdminModel, Depends(validateAdmin)],db: Annotated[Session, Depends(get_db)]):
    try:
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT,AdminRoleEnum.BUSPROVIDER]:
            return await  adminservice.tripManifest(response=response,db=db,tripId=tripId)
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)

    except Exception as ex:
        logger.error(ex)
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,data=[])
#train schedules
@router.get("/schedules", 
    response_model=SchedulesResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def get_schedules(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfSchedules(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SchedulesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/schedule/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def add_schedule(
    payload:AddScheduleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addSchedule(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/schedule/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def updateSchedule(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/schedule/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["schedule"])
async def deleteSchedule(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteSchedule(
            scheduleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
#seat
@router.get("/seats", 
    response_model=SeatsResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def get_seats(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfSeats(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SchedulesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/seat/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def addSeat(
    payload:AddSeatRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addSeat(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/seat/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def deleteSeat(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteSeat(
            seatId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )

# TICKET
@router.get("/tickets", 
    response_model=TicketsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_ticket(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await adminservice.listOfTickets(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/ticket/{id}", 
    response_model=TicketResponse,
    response_model_exclude_unset=True,tags=["ticket"])
async def get_ticket_details(
    id:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.getTicketDetail(ticketId=id,response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
#parks
@router.get("/parks", 
    response_model=ParksResponse,
    response_model_exclude_unset=True,tags=["park"])
async def get_parks(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return ParksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await  adminservice.listOfParks(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ParksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/park/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["park"])
async def addPark(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/park/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["park"])
async def updatePark(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/park/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["park"])
async def deletePark(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteRole(
            roleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
#bus
@router.get("/bus/routes", 
    response_model=BusRoutesResponse,
    response_model_exclude_unset=True,tags=["route"])
async def get_bus_routes(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfBusRoutes(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/bus/route/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["route"])
async def addBusRoute(
    payload:AddBusRouteRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addBusRoute(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get("/buses", 
    response_model=BusesResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def get_buses(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await  adminservice.listOfBuses(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/bus/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def addBus(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
    busImage: UploadFile= File(None),
    id: Optional[int] = Form(None),
    admin_id: int = Form(...),
    bus_type_id: int = Form(...),
    name: str = Form(...),
    bus_number: str = Form(...),
    description: Optional[str] = Form(None),
    tv: Optional[bool] = Form(False),
    camera: Optional[bool] = Form(False),
    airCondition: Optional[bool] = Form(False),
    availabilityStatus: str = Form(...),
    base_price: str = Form(...),
):
    try:
        logger.info(f"Received bus data: id={id}, admin_id={admin_id}, name={name}, bus_number={bus_number}, description={description}, tv={tv}, camera={camera}, airCondition={airCondition}, availabilityStatus={availabilityStatus}, base_price={base_price}")
        payload = AddBusRequest(
            id=id,
            admin_id=admin_id,
            name=name,
            bus_number=bus_number,
            description=description,
            tv=tv,
            camera=camera,
            airCondition=airCondition,
            availabilityStatus=availabilityStatus,
            base_price=base_price,
            bus_type_id=bus_type_id
        )
        if payload.id:
            return await adminservice.editBus(db=db,setting=setting,payload=payload,request=request,response=response,admin=admin,background_task=background_task)
        return await adminservice.addBus(db=db,setting=setting,payload=payload,request=request,response=response,admin=admin,background_task=background_task,busImage=busImage)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get("/buses/{providerId}", 
    response_model=BusesResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def get_buses_via_admin(
    providerId:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT,AdminRoleEnum.BUSPROVIDER]:
            return await  adminservice.listOfAdminBuses(response=response,db=db,providerId=providerId)
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/bus/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def updateBus(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/bus/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["bus"])
async def deleteBus(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteBus(
            busId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
#train
@router.get("/trains", 
    response_model=TrainsResponse,
    response_model_exclude_unset=True,tags=["train"])
async def get_trains(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await adminservice.listOfTrains(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/train/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["train"])
async def addTrain(
    payload:AddTrainRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if payload.id:
            return await adminservice.editTrain(db=db,setting=setting,payload=payload,request=request,response=response,admin=admin,background_task=background_task)
        return await adminservice.addTrain(db=db,setting=setting,payload=payload,request=request,response=response,admin=admin,background_task=background_task)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/train/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["train"])
async def updateTrain(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/train/{trainNumber}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["train"])
async def delete_train(
    trainNumber:str,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteTrain(
                db=db,
                request=request,
                response=response,
                admin=admin,
                setting=setting,
                background_task=background_task,
                trainNumber=trainNumber
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get("/notifications", 
    response_model=NotificationsResponse,
    response_model_exclude_unset=True,tags=["notification"])
async def get_notifications(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return NotificationsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await adminservice.listOfNotifications(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return NotificationsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/setting", 
    response_model=TicketsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_setting(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await adminservice.listOfTickets(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# Accounting
@router.get("/ledgers", 
    response_model=GLedgersResponse,
    response_model_exclude_unset=True,tags=["accounting"])
async def get_ledgers(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await glAccountingService.listOfLedgers(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return GLedgersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/ledger/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["accounting"])
async def add_ledger(
    payload:AddGLRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await glAccountingService.addLedger(
                payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/ledger/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["accounting"])
async def update_ledger(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/ledger/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["accounting"])
async def delete_ledger(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteRole(
            roleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# journal entries
@router.get("/journals", 
    response_model=JournalEntriesResponse,
    response_model_exclude_unset=True,tags=["journal"])
async def get_journals(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfSchedules(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SchedulesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/journal/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["journal"])
async def add_journal(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/journal/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["journal"])
async def update_journal(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/journal/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["journal"])
async def delete_journal(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteRole(
            roleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# commission rate
@router.get("/commissions", 
    response_model=CommissionsResponse,
    response_model_exclude_unset=True,tags=["commission"])
async def get_commissions(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await glAccountingService.listOfCommissions(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SchedulesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/commission/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["commission"])
async def add_commission(
    payload:AddCommissionRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await glAccountingService.addCommission(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/commission/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["commission"])
async def update_commission(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/commission/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["commission"])
async def delete_commission(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteRole(
            roleId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# discount rate
@router.get("/discounts", 
    response_model=ProvidersResponse,
    response_model_exclude_unset=True,tags=["discount"])
async def get_discounts(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await glAccountingService.listOfDiscounts(response=response,db=db,admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProvidersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/discount/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["discount"])
async def add_discount(
    payload:AddProviderRateRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await glAccountingService.addDiscount(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/discount/{id}/edit", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["discount"])
async def update_discount(
    payload:AddRoleRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.updateRole(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/discount/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["discount"])
async def delete_discount(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await glAccountingService.deleteDiscount(
            id=id,
            db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.patch("/discount/{id}/toggle", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["discount"])
async def toggle_discount(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await glAccountingService.toggleDiscount(
            setting=setting,
            id=id,
            db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )

# products
@router.get("/products", 
    response_model=ProductsResponse,
    response_model_exclude_unset=True,tags=["product"])
async def get_products(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await productservice.listOfProduct(response=response,db=db,admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/product/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def addProduct(
    payload:AddProductRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.addProduct(
                db=db,
                setting=setting,
                payload=payload,
                background_task=background_task,
                request=request,
                response=response,
                admin=admin
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/provider/refresh", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def refreshProvider(
    payload:AddProductTypeRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.refreshProvider(
                db=db,
                setting=setting,
                payload=payload,
                background_task=background_task,
                request=request,
                response=response,
                admin=admin
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/product/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def deleteProduct(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.deleteProduct(
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task,
                productId=id,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# biller
@router.get("/billers/{productId}", 
    response_model=ProductTypesResponse,
    response_model_exclude_unset=True,tags=["biller"])
async def get_billers(
    productId:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await productservice.listOfBillers(response=response,db=db,admin=admin,productId=productId)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/biller/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["biller"])
async def add_biller(
    payload:AddProductTypeRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.addBiller(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/biller/switch-provider",response_model=BaseResponse,)
async def add_switch(
    payload:SwitchProviderRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.switchBillerServiceProvider(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/biller/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["biller"])
async def delete_biller(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.deleteBiller(
            billerId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# packages
@router.get("/packages/{billerId}", 
    response_model=PackagesResponse,
    response_model_exclude_unset=True,tags=["package"])
async def get_packages(
    billerId: int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await productservice.listOfPackages(
                billerId=billerId,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/package/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["package"])
async def add_package(
    payload:AddPackageRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservice.addPackage(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/package/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["package"])
async def delete_package(
    id:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await productservice.deletePackage(
            packageId=id,
                db=db,
                response=response,
                admin=admin,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# cashout
@router.get("/cashouts", 
    response_model=CashoutsResponse,
    response_model_exclude_unset=True)
async def get_cashouts(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return paymentservice.listOfCashout(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/cashout/{id}", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_details(
    id:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.getCashoutDetail(cashoutId=id,response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/cashout-analytics", 
    response_model=CashoutsResponse,
    response_model_exclude_unset=True,tags=["analytics"])
async def get_cashout_analytics(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.cashOutsAnalytics(response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/banks",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def getBanks(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
):
    try:
        return await paymentservice.getbanks(response=response,setting=setting)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.post("/cashout/bank-verification",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_verification(
    payload: AddCashoutAccountRequest,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
):
    try:
        return await adminservice.verifyCashoutAccount(
                payload=payload,
                response=response,
                setting=setting,
                admin=admin,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/cashout/add-bank-account",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_add_bank(
    payload: AddCashoutAccountRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addCashoutBankRecipient(
                payload=payload,
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/cashout/withdraw",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_withdrawal_request(
    payload: CashoutWithdrawalRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.cashoutWithdrawal(
                payload=payload,
                response=response,
                request=request,
                db=db,
                setting=setting,
                admin=admin,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/cashout/limit",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_limit_increase(
    payload: CashoutLimitRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.cashoutLimitChange(
                payload=payload,
                response=response,
                request=request,
                db=db,
                setting=setting,
                admin=admin,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/cashout/confirmation-check",
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_confirmation_check(
    payload: CashoutConfirmationRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.cashoutConfirmationCheck(
                payload=payload,
                response=response,
                request=request,
                db=db,
                setting=setting,
                admin=admin,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/cashout/{id}/approve", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_approval(
    id:int,
    response: Response,
    request: Request,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.approveCashout(
            cashoutId=id,
            request=request,
                response=response,
                db=db,
                admin=admin,
                setting=setting,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get("/cashout/{id}/reject", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["cashout"])
async def cashout_reject(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.rejectCashout(
            cashoutId=id,
            request=request,
                response=response,
                db=db,
                admin=admin,
                setting=setting,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# analytics
@router.get("/services", 
    response_model=ProductTypesResponse,
    response_model_exclude_unset=True,tags=["product"])
async def get_product_types(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return await adminservice.listOfBiller(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/providers", 
    response_model=AdminsResponse,
    response_model_exclude_unset=True,tags=["product"])
async def get_providers(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.listOfProviders(response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return AdminsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/ticket-analytics", 
    response_model=TicketsResponse,
    response_model_exclude_unset=True,tags=["analytics"])
async def get_ticket_analytics(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.ticketsAnalytics(response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
#Support Tiocket
@router.get("/support-tickets", 
    response_model=SupportTicketsResponse,
    response_model_exclude_unset=True,tags=["support"])
async def get_support_tickets(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return TicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await adminservice.listOfSupportTickets(
                response=response,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return SupportTicketsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/seat/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def addSeat(
    payload:AddSeatRequest,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.addSeat(
            payload=payload,
                db=db,
                setting=setting,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.delete("/seat/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["seat"])
async def deleteSeat(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.deleteSeat(
            seatId=id,
                db=db,
                request=request,
                response=response,
                admin=admin,
                background_task=background_task
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
# payments 
@router.get("/payments", 
    response_model=PaymentsResponse,
    response_model_exclude_unset=True,name="get customer payemnt")
async def get_Admin_payments(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return paymentservice.adminPayments(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/payment-analytics", 
    response_model=PaymentsResponse,
    response_model_exclude_unset=True,tags=["analytics"])
async def get_payment_analytics(
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.paymentsAnalytics(response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return AdminsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# customers
@router.get("/customers", 
    response_model=CustomersResponse,
    response_model_exclude_unset=True,tags=["customer"],name="get customer payemnt")
async def get_customers(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(default=util.get_first_day_of_month()),
    endDate: Optional[str] = Query(str(date.today())),
):
    try:
        if admin:
            if startDate and endDate:
                start = datetime.strptime(startDate, "%Y-%m-%d")
                end = datetime.strptime(endDate, "%Y-%m-%d")
                if end < start:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return CustomersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="End date must be greater than or equal to start date.")
            return await adminservice.listOfCustomer(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,
                startDate=startDate,
                endDate=endDate)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomersResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/customer/{id}", 
    response_model=CustomerResponse,
    response_model_exclude_unset=True,tags=["customer"])
async def get_customer_details(
    id:int,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await adminservice.getCustomerDetail(customerId=id,response=response,db=db,admin=admin)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomerResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.get("/customer/{id}/resetpassword", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["customer"])
async def reset_customer_password(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.resetCustomerAccountPassword(
            customerId=id,
            request=request,
                response=response,
                db=db,
                admin=admin,
                setting=setting,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get("/customer/{id}/disable-account", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["customer"])
async def disable_customer_account(
    id:int,
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await adminservice.toggleCustomerAccountStatus(
            customerId=id,
            request=request,
                response=response,
                db=db,
                admin=admin,
                setting=setting,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
