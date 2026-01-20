
import logging
from utils import util
from models.model import *
from utils.constant import *
from schemas.customer import *
from sqlalchemy.orm import Session
from schemas.setting import Setting
from schemas.product import *
from schemas.package import *
from schemas.product_type import *
from schemas.admin import ProvidersResponse
from schemas.station import StationsResponse
from schemas.route import RoutesResponse,RouteResponse,TrainRoutesResponse,TrainRouteResponse
from schemas.bus_route import BusRoutesResponse,BusRouteResponse
from fastapi import Response,Request,status
from models.queries import productQuery,queries
from schemas.beneficiary import *
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
logger = logging.getLogger(__name__)


def getAllBill(db: Session):
    return productQuery.get_all_bill(db=db)
def getSingleBill(db: Session, id: int):
    bill = productQuery.get_single_bill_by_id(db=db, id=id)
    logger.info(bill)
    return bill
def getAllBillers(db: Session):
    return productQuery.get_all_biller(db=db)
def getSingleBiller(db: Session, id: int):
    return productQuery.get_single_biller_by_id(db=db, id=id)
async def searchMovablesRoutes(response: Response,db: Session,user: Customer,departure: str,arrival: str,mode: str,latitude:str,longitude:str):
    try:
        logger.info(f"Started searching for {mode} route by {user.firstname}")
        data = []
        message = None
        if departure and arrival:
            logger.info(f"Searching for {mode} route from {departure} to {arrival}")
            route = queries.getBusRoutesByStations(db=db,departure=departure,arrival=arrival,mode=mode)
            if route:
                return BusRoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=route,message=message)
            message = f"No {mode} route found from {departure} to {arrival}"
        if longitude and latitude:
            data = queries.getAdminRoutes(db=db,role=AdminRoleEnum.BUSPROVIDER,latitude=float(latitude),longitude=float(longitude),radius_km=20)
            if data:
                return BusRoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data,message=message)
        data = queries.query_routes(db=db,mode=mode)
        return BusRoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data,message=message)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusRoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def searchTrainRoutes(response: Response,db: Session,user: Customer,departure: str,arrival: str,mode: str,latitude:str,longitude:str):
    try:
        logger.info(f"Started searching for train from {departure} to {arrival} latitude {latitude} longtitude {longitude} at {datetime.now()}") 
        data = []
        if departure and arrival:
            logger.info(f"Searching for {mode} route from {departure} to {arrival}")
            route = queries.getTrainRoutesByStations(db=db,departure=departure,arrival=arrival,mode=mode)
            if route:
                return TrainRoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=route)
        if longitude and latitude:
            data = queries.getAvailableTrainRoutes(db=db,latitude=float(latitude),longitude=float(longitude),radius_km=20)
            #datad = queries.getAdminRoutes(db=db,role=AdminRoleEnum.BUSPROVIDER,latitude=float(latitude),longitude=float(longitude),radius_km=5)
            #logger.info(datad)
            #for admin in admins:
            #    admin.routes = [route for route in admin.routes if admin.routes and util.is_within_radius(lat1=float(route.sourceStation.lat),lon1=float(route.sourceStation.long),lat2=float(latitude),lon2=float(longitude),radius_km=50)]
            #    data.append(admin)
            #logger.info(data)
            return TrainRoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TrainRoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def searchTrainByRoute(routeId:int,mode:str,request: Request,response: Response,setting: Setting,db: Session,user: Customer):
    try:
        logger.info(f"Started searching for train from route {routeId} mode {mode}") 
        route = queries.queryRouteByIdAndMode(db=db,routeId=routeId,mode=mode)
        if route:
            return RouteResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=route)
        return RouteResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def stations(mode:str,request: Request,response: Response,setting: Setting,db: Session,user: Customer):
    try:
        logger.info(f"Started getting stations")
        if mode.lower() == "bus":
            data = queries.query_stations(db=db,mode=mode)
        elif mode == "train":
            data = queries.query_stations(db=db,mode=mode)
        else:
            data = queries.query_stations(db=db,mode=mode)
        if not data:
            data = queries.query_stations(db=db,mode=mode)
        data = []
        data = queries.query_stations(db=db,mode=mode)
        if data:
            return StationsResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
        return StationsResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def availableRoutes(mode:str,request: Request,response: Response,setting: Setting,db: Session,user: Customer):
    try:
        logger.info(f"Started getting routes............")
        data = []
        data = queries.query_routes(db=db,mode=mode)
        if data:
            return RoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
        return RoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def getBeneficiaries(db: Session,response: Response,transType:str,user:Customer):
    beneficiaries = productQuery.queryBeneficiaryByTransactionType(db=db,transactionType=transType,userId=user.id)
    if beneficiaries:
        return BeneficiariesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=beneficiaries)
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BeneficiariesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
def addBeneficiary(db: Session,request:Request,response:Response,payload:AddBeneficiaryRequest,user:CustomerModel):
    existedBeneficiary = productQuery.querySinglebeneficiary(db=db,transactionType=payload.transaction_type,userId=user.id,customerId=payload.customerId)
    if existedBeneficiary:
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ALREADYEXIST)
    biller = productQuery.get_single_biller_by_billerId(db=db,billerId=payload.billercode)
    if biller:
        newBeneficiary = BeneficiaryModel(
            identifier=util.generateId(length=6),
        transaction_type = payload.transaction_type,
        nickname = payload.nickname,
        customerId = payload.customerId,
        billercode = biller.billerId,
        billername =biller.billerName,
        logo = biller.logo,
        user_id = user.id)
        created = productQuery.create(db=db,model=newBeneficiary)
        if created:
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
def deleteBeneficiary(db: Session,beneficiaryId:str,user:Customer):
    deleted = productQuery.deleteRecord(db=db,id=beneficiaryId,userId=user.id)
    if deleted:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
async def getBusprovider(response: Response,setting: Setting,db: Session,user: Customer):
    try:
        logger.info(f"Started getting all bus provider at {datetime.now()}")
        return ProvidersResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getBusProvider(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProvidersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getBusproviderRoutes(response: Response,db: Session,adminId:int):
    try:
        logger.info(f"Started getting all bus provider at {datetime.now()}")
        return BusRoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getBusRoutesByProvider(db=db,adminId=adminId))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusRoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getTrainprovider(response: Response,setting: Setting,db: Session,user: Customer):
    try:
        logger.info(f"Started getting all bus provider at {datetime.now()}")
        return ProvidersResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.getTrainProvider(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProvidersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getTrainproviderRoutes(response: Response,db: Session,adminId:int):
    try:
        logger.info(f"Started getting all train provider at {datetime.now()}")
        return RoutesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.query_train_routes_by_provider(db=db,adminId=adminId))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return RoutesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# admin products
async def listOfProduct(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying products")
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ProductsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        else:
            return ProductsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=productQuery.getProducts(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def listOfProductBiller(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying products")
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ProductsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
        else:
            return ProductsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=productQuery.getProducts(db=db))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addProduct(db: Session,setting: Setting,payload: AddProductRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started product at {datetime.now()}")
        existing = productQuery.getProductById(db=db,productId=payload.id)
        if existing:
            subject = "Product Update"
            existing.name = payload.name
            existing.vasType = payload.vasType
            existing.status = payload.status
            existing.customerField = payload.customerField
            existing.description = payload.description
            existing.updated_at=datetime.now()
        else:
            subject = "New Product"
            existing = ProductModel(
                name =payload.name,
                vasType = payload.vasType,
                status = payload.status,
                customerField = payload.customerField,
                description = payload.description,
                created_at=datetime.now(),updated_at=datetime.now(),)
        created = queries.create(db=db, model=existing)
        if created:
            email_body = util.templates.TemplateResponse("product.html",{"request": request, "product": created,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=subject,toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteProduct(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,productId: int):
    try:
        logger.info(f"started deleting product {productId} at {datetime.now()}")
        deleted = productQuery.deleteProduct(db=db,productId=productId)
        if deleted:
            response.status_code = status.HTTP_200_OK
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# billers
async def listOfBillers(response: Response,db: Session,admin: AdminModel,productId:int):
    try:
        logger.info(f"started querying biller by product ID")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            return ProductTypesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=productQuery.getBillersByProductId(db=db,productId=productId))
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ProductTypesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductTypesResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addBiller(db: Session,setting: Setting,payload: AddProductTypeRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started product at {datetime.now()}")
        existing = productQuery.getProductTypeById(db=db,billerId=payload.id)
        if existing:
            subject = "Biller Update"
            existing.billerId = payload.billerId
            existing.billerName = payload.billerName
            existing.billerType = payload.billerType
            existing.customerField = payload.customerField
            existing.hasAddons = payload.hasAddons
            existing.hasLookup = payload.hasLookup
            existing.hasPackages = payload.hasPackages
            existing.status=payload.status
            existing.maxAmountLimit=payload.maxAmountLimit
            existing.minAmountLimit=payload.minAmountLimit
            existing.updated_at=datetime.now()
        else:
            subject = "New Biller"
            existing = ProductTypeModel(
                product_id=payload.product_id,
                billerId =payload.billerId,
                billerName = payload.billerName,
                status = payload.status,
                customerField = payload.customerField,
                hasAddons = payload.hasAddons,
                hasLookup = payload.hasLookup,
                hasPackages = payload.hasPackages,
                maxAmountLimit = payload.maxAmountLimit,
                minAmountLimit = payload.minAmountLimit,
                created_at=datetime.now(),updated_at=datetime.now(),)
        created = productQuery.create(db=db, model=existing)
        if created:
            email_body = util.templates.TemplateResponse("product.html",{"request": request, "product": created,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=subject,toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteBiller(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,billerId: int):
    try:
        logger.info(f"started deleting product {billerId} at {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            deleted = productQuery.deleteBiller(db=db,billerId=billerId)
            if deleted:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# packages
async def listOfPackages(response: Response,db: Session,admin: AdminModel,billerId: int):
    try:
        logger.info(f"started querying biller by product ID")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            return PackagesResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=productQuery.getPackagesByBillerId(db=db,billerId=billerId))
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ProductsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addPackage(db: Session,setting: Setting,payload: AddPackageRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started package at {datetime.now()}")
        existing = productQuery.getPackageById(db=db,packageId=payload.id)
        if existing:
            subject = "Package Update"
            existing.billerId = payload.billerId
            existing.packageCode = payload.packageCode
            existing.amount = payload.amount
            existing.currencyCode = payload.currencyCode
            existing.hasValidity = payload.hasValidity
            existing.description = payload.description
            existing.validity = payload.validity
            existing.product_type_id =payload.product_type_id,
            existing.status=payload.status
            existing.updated_at=datetime.now()
        else:
            subject = "New Package"
            existing = PackageModel(
                billerId =payload.billerId,
                product_type_id =payload.product_type_id,
                packageCode = payload.packageCode,
                status = payload.status,
                amount = payload.amount,
                currencyCode = payload.currencyCode,
                hasValidity = payload.hasValidity,
                description = payload.description,
                validity = payload.validity,
                created_at=datetime.now(),updated_at=datetime.now(),)
        created = productQuery.create(db=db, model=existing)
        if created:
            email_body = util.templates.TemplateResponse("product.html",{"request": request, "product": created,},)
            background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=subject,toAddress=admin.email,)
            return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deletePackage(db: Session,response: Response,admin:AdminModel,packageId: int):
    try:
        logger.info(f"started deleting package {packageId} at {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN]:
            deleted = productQuery.deletePackage(db=db,packageId=packageId)
            if deleted:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
