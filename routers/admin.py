from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Query,
    Request,
    BackgroundTasks,
)
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
from services import adminservice
from schemas.admin import *
from schemas.role import *
from schemas.station import StationsResponse
from schemas.route import RoutesResponse
from schemas.train import TrainsResponse
from schemas.bus import BusesResponse
from schemas.park import ParksResponse
from schemas.ticket import TicketsResponse
from schemas.notification import NotificationsResponse
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
        return adminservice.authenticateUser(
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
            return adminservice.profile(
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
        return adminservice.createAccount(request=request,response=responses,setting=Setting,db=db,payload=payload,background_task=background_task)
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
):
    try:
        return adminservice.listOfAdmins(
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
        return adminservice.analytics(
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
            return adminservice.getDashboardByProducts(
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
# station
@router.get("/stations", 
    response_model=StationsResponse,
    response_model_exclude_unset=True,tags=["station"])
async def get_stations(
    request: Request,
    response: Response,
    admin: Annotated[AdminModel, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if admin:
            return adminservice.listOfStations(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)

    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/station/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["station"])
async def addStation(
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
            return adminservice.listOfRoutes(
                request=request,
                response=response,
                setting=setting,
                db=db,
                admin=admin,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
@router.post("/route/add", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["route"])
async def addRoute(
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
            return adminservice.listOfTickets(
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
            return adminservice.listOfParks(
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
            return adminservice.listOfBuses(
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
            return adminservice.listOfTrains(
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
@router.delete("/train/{id}/delete", 
    response_model=BaseResponse,
    response_model_exclude_unset=True,tags=["train"])
async def deleteTraine(
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
            return adminservice.listOfNotifications(
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
            return adminservice.listOfTickets(
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

