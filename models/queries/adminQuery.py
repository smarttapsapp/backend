from sqlalchemy.orm import Session
from sqlalchemy import desc,or_
from typing import List
from sqlalchemy.sql import select,update,case
from models.model import *
import logging
from datetime import datetime,date

logger = logging.getLogger(__name__)
def getBillerByBillerId(db: Session, billerId: str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerId == billerId).first()
def save(db: Session, account: AccountModel):
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
def save_many(db: Session, models: List[object]):
    db.add_all(models)
    db.commit()
def getRoleByTag(db: Session,tag:str):
    return db.query(RoleModel).filter(RoleModel.tag == tag).first()
def getRoleByRoleType(db: Session,roleType:str):
    return db.query(RoleModel).filter(RoleModel.roleType == roleType).first()
def getRoleById(db: Session,roleId:int):
    return db.query(RoleModel).filter(RoleModel.id == roleId).first()
def deleteRole(db: Session ,roleId:int):
    logger.info(f"started deleting role {roleId}")
    db.query(RoleModel).filter(RoleModel.id == roleId).delete()
    db.commit()
    return True
def countCustomers(db: Session):
    return db.query(CustomerModel).count()
def countActiveCustomers(db: Session):
    return db.query(CustomerModel).count()
def customersAnalytics(db: Session):
    row = db.query(
    func.count().label("total_customers"),
    func.sum(case((CustomerModel.account_status == "active", 1), else_=0)).label("active_customers"),
    func.sum(case((CustomerModel.account_status == "registration", 1), else_=0)).label("reg_customers"),
    func.sum(case((CustomerModel.account_status == "inactive", 1), else_=0)).label("inactive_customers"),
    func.sum(case((CustomerModel.account_status == "blocked", 1), else_=0)).label("blocked_customers"),
    func.sum(case((CustomerModel.account_status == "disabled", 1), else_=0)).label("disabled_customers")
).one()
    return dict(row._mapping)
def creditPaymentsAnalytics(db: Session):
    row = db.query(
    func.count().label("total_payment"),
    func.sum(PaymentModel.amount).label("total_amount"),
    func.sum(case((PaymentModel.status == "success", 1), else_=0)).label("successful_payments"),
    func.sum(case((PaymentModel.status == "failed", 1), else_=0)).label("failed_payments"),
    func.sum(case((PaymentModel.status == "initialize", 1), else_=0)).label("pending_payments"),
    func.sum(case((PaymentModel.status == "success", PaymentModel.amount), else_=0)).label("successful_amount"),
    func.sum(case((PaymentModel.status == "initialize", PaymentModel.amount), else_=0)).label("pending_amount"),
    func.sum(case((PaymentModel.status == "failed", PaymentModel.amount), else_=0)).label("failed_amount")
).filter(PaymentModel.payment_type == "CREDIT").one()
    return dict(row._mapping)
def debitPaymentsAnalytics(db: Session):
    row = db.query(
    func.count().label("total_payment"),
    func.sum(PaymentModel.amount).label("total_amount"),
    func.sum(case((PaymentModel.status == "success", 1), else_=0)).label("successful_payments"),
    func.sum(case((PaymentModel.status == "initialize", 1), else_=0)).label("pending_payments"),
    func.sum(case((PaymentModel.status == "failed", 1), else_=0)).label("failed_payments"),
    func.sum(case((PaymentModel.status == "success", PaymentModel.amount), else_=0)).label("successful_amount"),
    func.sum(case((PaymentModel.status == "initialize", PaymentModel.amount), else_=0)).label("pending_amount"),
    func.sum(case((PaymentModel.status == "failed", PaymentModel.amount), else_=0)).label("failed_amount")
).filter(PaymentModel.payment_type == "DEBIT").one()
    return dict(row._mapping)
def admin(db: Session,username:str):
    return db.query(AdminModel).filter(AdminModel.email ==username).first()
def getAdminByRole(db: Session,id:int):
    return db.query(AdminModel).filter(AdminModel.role_id ==id).first()
def getAdminByCustomerId(db: Session,id:int):
    return db.query(AdminModel).filter(AdminModel.customer_id ==id).first()
def getAdminProvider(db:Session):
    return db.query(AdminModel).join(RoleModel).filter(RoleModel.tag.in_([AdminRoleEnum.PROVIDER,AdminRoleEnum.BUSPROVIDER,AdminRoleEnum.TRAINPROVIDER])).order_by(desc(AdminModel.created_at)).all()
def getBusProvider(db:Session):
    return db.query(AdminModel).join(RoleModel).filter(RoleModel.tag == AdminRoleEnum.BUSPROVIDER).order_by(desc(AdminModel.created_at)).all()
def getTrainProvider(db:Session):
    return db.query(AdminModel).join(RoleModel).filter(RoleModel.tag == AdminRoleEnum.TRAINPROVIDER).order_by(desc(AdminModel.created_at)).all()
def getAllRole(db: Session,adminId:int=None):
    return db.query(RoleModel).filter(RoleModel.roleType == AdminTypeEnum.INTERNAL).order_by(desc(RoleModel.created_at)).all()
def getRole(db: Session,roleId:int=None):
    return db.query(RoleModel).filter(RoleModel.id ==roleId).first()
def getRoleViaTag(db: Session,tag:str=None):
    return db.query(RoleModel).filter(RoleModel.tag ==tag).first()
def getAllAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).join(RoleModel).filter(RoleModel.roleType == AdminTypeEnum.INTERNAL).order_by(desc(AdminModel.created_at)).all()
def getAllAdminByRole(db: Session,role:AdminTypeEnum):
    return db.query(AdminModel).join(RoleModel).filter(RoleModel.roleType == role).order_by(desc(AdminModel.created_at)).all()
def getAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).filter(AdminModel.id ==adminId).first()
def getAdminIdentifier(db: Session, id: str):
    return db.query(AdminModel).filter(AdminModel.identifier == id).first()
# trains
def getTrains(db: Session,adminId:int=None):
    if adminId:
        return db.query(TrainModel).filter(TrainModel.admin_id ==adminId,TrainModel.isdelete == False).order_by(desc(TrainModel.created_at)).all()
    return db.query(TrainModel).filter(TrainModel.isdelete == False).order_by(desc(TrainModel.created_at)).all()
def getTrain(db: Session,trainNumber:str):
    return db.query(TrainModel).filter(TrainModel.trainNumber==trainNumber).first()
def deleteTrain(db: Session,id:str):
    return db.query(TrainModel).filter(or_(TrainModel.id == id, TrainModel.identifier == id)).delete()
def deleteTrainSchedules(db: Session,ids:list[str]):
    logger.info(f"Deleting train schedules with IDs: {ids}")
    return db.query(TrainScheduleModel).filter(TrainScheduleModel.identifier.in_(ids)).delete()
def countTrains(db: Session):
    return db.query(TrainModel).count()
def getTrainsByBusiness(db: Session,adminId:int=None):
    return db.query(TrainModel).filter(TrainModel.route_id ==adminId).order_by(desc(TrainModel.created_at)).all()
#bus types
def getBusTypes(db: Session,adminId:int=None):
    if adminId:
        return db.execute(select(BusTypeModel, AdminModel.companyName).join(AdminModel, AdminModel.id == BusTypeModel.admin_id).filter(BusTypeModel.admin_id ==adminId).order_by(desc(BusTypeModel.created_at))).mappings().all()
    return db.execute(select(
        BusTypeModel.id,
        BusTypeModel.name,
        BusTypeModel.admin_id,
        BusTypeModel.total_seats,
        BusTypeModel.created_at, AdminModel.companyName).join(AdminModel, AdminModel.id == BusTypeModel.admin_id).order_by(desc(BusTypeModel.created_at))).mappings().all()
def getBusTypeId(db: Session, id: int):
    return db.execute(select(BusTypeModel).join(AdminModel).filter(BusTypeModel.id == id)).scalars().first()
def deleteBusType(db: Session,id:int):
    return db.query(BusTypeModel).filter(BusTypeModel.id ==id).delete()
#buses
def getBusesOld(db: Session,adminId:int=None):
    if adminId:
        return db.query(BusModel).filter(BusModel.admin_id ==adminId,BusModel.isdelete == False).order_by(desc(BusModel.created_at)).all()
    return db.query(BusModel).filter(BusModel.isdelete == False).order_by(desc(BusModel.created_at)).all()
def getBuses(db: Session,adminId:int=None):
    if adminId:
        return db.execute(select(
        BusModel.id,
        BusModel.identifier,
        BusModel.name,
        BusModel.bus_number,
        BusModel.bus_capacity,
        BusModel.busImage,
        BusModel.admin_id,
        BusModel.billerId,
        BusModel.description,
        BusModel.types,
        BusModel.tv,
        BusModel.camera,
        BusModel.airCondition,
        BusModel.base_price,
        BusModel.created_at, 
        AdminModel.companyName).join(AdminModel, AdminModel.id == BusModel.admin_id).filter(BusModel.admin_id ==adminId).order_by(desc(BusModel.created_at))).mappings().all()
    return db.execute(select(
        BusModel.id,
        BusModel.identifier,
        BusModel.name,
        BusModel.bus_number,
        BusModel.bus_capacity,
        BusModel.busImage,
        BusModel.admin_id,
        BusModel.billerId,
        BusModel.description,
        BusModel.types,
        BusModel.tv,
        BusModel.camera,
        BusModel.airCondition,
        BusModel.base_price,
        BusModel.created_at, 
        AdminModel.companyName).join(AdminModel, AdminModel.id == BusModel.admin_id).order_by(desc(BusModel.created_at))).mappings().all()

def getBusId(db: Session,id:int):
    return db.query(BusModel).filter(BusModel.id == id).first()
def getBus(db: Session,busNumber:str):
    return db.query(BusModel).filter(BusModel.bus_number == busNumber).first()
def getBusesByIds(db:Session,ids:list[int],adminId:int=None):
    if adminId:
        return db.query(BusModel).filter(BusModel.admin_id == adminId).filter(BusModel.id.in_(ids)).all()
    return db.query(BusModel).filter(BusModel.id.in_(ids)).all()
def deleteBus(db: Session,id:int):
    return db.query(BusModel).filter(BusModel.id ==id).delete()
def countBuses(db: Session):
    return db.query(BusModel).count()
def getBusesByBusiness(db: Session,parkId:int=None):
    return db.query(BusModel).filter(BusModel.park_id ==parkId).order_by(desc(BusModel.created_at)).all()
# schedules
def getBusSchedules(db: Session,adminId:int=None):
    if adminId:
        return db.query(BusScheduleModel).filter(BusScheduleModel.admin_id ==adminId).order_by(desc(BusScheduleModel.created_at)).all()
    return db.execute(
    select(
        BusScheduleModel.id,
        BusScheduleModel.identifier,
        BusScheduleModel.timeOfOperation,
        BusScheduleModel.total_seats,
        BusScheduleModel.status,
        BusScheduleModel.trip_Date,
        BusScheduleModel.admin_id,
        BusScheduleModel.arrivalTime,
        BusScheduleModel.booked_seats,
        BusScheduleModel.trip_Date,
        BusScheduleModel.bus_id,
        BusScheduleModel.bus_route_id,
        BusScheduleModel.departureTime,
        BusScheduleModel.price,
        BusScheduleModel.created_at,
        AdminModel.companyName,
        BusModel.name.label("busName"),
        BusRouteModel.routeName,
    )
    .join(AdminModel, AdminModel.id == BusScheduleModel.admin_id)
    .join(BusModel, BusModel.id == BusScheduleModel.bus_id)
    .join(BusRouteModel, BusRouteModel.id == BusScheduleModel.bus_route_id)
    .filter(BusScheduleModel.isdelete == False)
    .order_by(desc(BusScheduleModel.created_at))
).mappings().all()
def getBusSchedulesByIds(db:Session,ids:list[int],adminId:int=None):
    if adminId:
        return db.query(BusScheduleModel).filter(BusScheduleModel.admin_id ==adminId).filter(BusScheduleModel.id.in_(ids)).all()
    return db.query(BusScheduleModel).filter(BusScheduleModel.id.in_(ids)).all()
def getBusScheduleById(db: Session,scheduleId:int):
    return db.query(BusScheduleModel).filter(BusScheduleModel.id == scheduleId).first()
def deleteBusSchedule(db: Session ,scheduleId:int):
    deleted = db.query(BusScheduleModel).filter(BusScheduleModel.id == scheduleId).delete()
    if deleted:
        db.commit()
        return True
    return False

# stations
def getstations(db: Session,mode:MovableEnum,adminId:int=None):
    if adminId:
        return db.execute(select(
        StationModel.id,
        StationModel.identifier,
        StationModel.stationName,
        StationModel.location,
        StationModel.status,
        StationModel.parkImage,
        StationModel.admin_id,
        StationModel.contact,
        StationModel.description,
        StationModel.address,
        StationModel.lat,
        StationModel.long,
        StationModel.policy,
        StationModel.mode,
        StationModel.created_at, 
        AdminModel.companyName).join(AdminModel, AdminModel.id == StationModel.admin_id).filter(StationModel.admin_id == adminId,StationModel.mode == mode.value,StationModel.isdelete == False)).mappings().all()
    return db.execute(select(
        StationModel.id,
        StationModel.identifier,
        StationModel.stationName,
        StationModel.location,
        StationModel.status,
        StationModel.parkImage,
        StationModel.admin_id,
        StationModel.contact,
        StationModel.description,
        StationModel.address,
        StationModel.lat,
        StationModel.long,
        StationModel.policy,
        StationModel.mode,
        StationModel.created_at, 
        AdminModel.companyName).join(AdminModel, AdminModel.id == StationModel.admin_id).filter(StationModel.mode == mode.value,StationModel.isdelete == False).order_by(desc(StationModel.created_at))).mappings().all()
def getStationById(db: Session,stationId:str):
    return db.query(StationModel).filter(StationModel.identifier == stationId).first()
def deleteStation(db: Session ,stationId:int):
    return db.query(StationModel).filter(StationModel.id == stationId).delete()
# routes
def getRoutes(db: Session,adminId:int=None):
    if adminId:
        return db.query(TrainRouteModel).filter(TrainRouteModel.admin_id ==adminId,TrainRouteModel.isdelete == False).order_by(desc(TrainRouteModel.created_at)).all()
    return db.query(TrainRouteModel).filter(TrainRouteModel.isdelete == False).order_by(desc(TrainRouteModel.created_at)).all()
def getBusRoutes(db: Session,adminId:int=None):
    if adminId:
        return db.execute(select(
        BusRouteModel.id,
        BusRouteModel.identifier,
        BusRouteModel.routeName,
        BusRouteModel.admin_id,
        BusRouteModel.sourceStation_id,
        BusRouteModel.destinationStation_id,
        BusRouteModel.baseprice,
        BusRouteModel.created_at,
        BusRouteModel.mode,
        AdminModel.companyName).join(AdminModel, AdminModel.id == BusRouteModel.admin_id).filter(BusRouteModel.admin_id ==adminId).order_by(desc(BusRouteModel.created_at))).mappings().all()
    return db.execute(select(
        BusRouteModel.id,
        BusRouteModel.identifier,
        BusRouteModel.routeName,
        BusRouteModel.admin_id,
        BusRouteModel.sourceStation_id,
        BusRouteModel.destinationStation_id,
        BusRouteModel.baseprice,
        BusRouteModel.created_at,
        BusRouteModel.mode,
        AdminModel.companyName).join(AdminModel, AdminModel.id == BusRouteModel.admin_id).order_by(desc(BusRouteModel.created_at))).mappings().all()
def getBusRouteById(db: Session,routeId:int):
    return db.query(BusRouteModel).filter(BusRouteModel.id == routeId).first()
def getRouteById(db: Session,routeId:int):
    return db.query(TrainRouteModel).filter(TrainRouteModel.id == routeId).first()
def getRouteByStartStopStation(db: Session,start:int,stop:int,adminId:int):
    return db.query(TrainRouteModel).filter(TrainRouteModel.admin_id == adminId).filter(TrainRouteModel.sourceStation_id == start).filter(TrainRouteModel.destinationStation_id == stop).first()
def getRouteByStartStopIdentifier(db: Session,start:str,stop:str,adminId:int):
    return db.query(TrainRouteModel).filter(TrainRouteModel.admin_id == adminId).filter(TrainRouteModel.sourceStation_id == start).filter(TrainRouteModel.destinationStation_id == stop).first()
def getRoutesByIds(db:Session,ids:list[str],adminId:int=None):
    if adminId:
        return db.query(TrainRouteModel).filter(TrainRouteModel.admin_id ==adminId,TrainRouteModel.isdelete == False).filter(TrainRouteModel.identifier.in_(ids)).all()
    return db.query(TrainRouteModel).filter(TrainRouteModel.identifier.in_(ids)).filter(TrainRouteModel.isdelete == False).order_by(desc(TrainRouteModel.created_at)).all()
def deleteRoute(db: Session ,routeId:str):
    return db.query(TrainRouteModel).filter(TrainRouteModel.identifier == routeId).delete()
# schedules
def getSchedules(db: Session,adminId:int=None):
    if adminId:
        return db.query(ScheduleModel).filter(ScheduleModel.admin_id ==adminId).order_by(desc(ScheduleModel.created_at)).all()
    return db.query(ScheduleModel).all()
def getSchedulesByIds(db:Session,ids:list[int],adminId:int=None):
    if adminId:
        return db.query(ScheduleModel).filter(ScheduleModel.admin_id ==adminId).filter(ScheduleModel.id.in_(ids)).all()
    return db.query(ScheduleModel).filter(ScheduleModel.id.in_(ids)).all()
def getScheduleById(db: Session,scheduleId:int):
    return db.query(ScheduleModel).filter(ScheduleModel.id == scheduleId).first()
def deleteSchedule(db: Session ,scheduleId:int):
    deleted = db.query(ScheduleModel).filter(ScheduleModel.id == scheduleId).delete()
    if deleted:
        db.commit()
        return True
    return False
# seat
def getSeats(db: Session,adminId:int=None):
    if adminId:
        return db.query(SeatModel).filter(SeatModel.admin_id ==adminId).order_by(desc(SeatModel.created_at)).all()
    return db.query(SeatModel).all()
def getSeatsByIds(db:Session,ids:list[int],adminId:int=None):
    if adminId:
        return db.query(SeatModel).filter(SeatModel.admin_id ==adminId).filter(SeatModel.id.in_(ids)).all()
    return db.query(SeatModel).filter(SeatModel.id.in_(ids)).all()
def getSeatById(db: Session,seatId:int):
    return db.query(SeatModel).filter(SeatModel.id == seatId).first()
def deleteSeat(db: Session ,seatId:int):
    return db.query(SeatModel).filter(SeatModel.id == seatId).delete()

# parks
def getParks(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(ParkModel).filter(ParkModel.created_at.between(start,end)).order_by(desc(ParkModel.created_at)).all()
    return db.query(ParkModel).order_by(desc(ParkModel.created_at)).all()
def getParkByIds(db:Session,ids:list[int],adminId:int=None):
    if adminId:
        return db.query(ParkModel).filter(ParkModel.admin_id ==adminId).filter(ParkModel.id.in_(ids)).all()
    return db.query(ParkModel).filter(ParkModel.id.in_(ids)).all()
def getParkById(db: Session,scheduleId:int):
    return db.query(ParkModel).filter(ParkModel.id == scheduleId).first()
def deletePark(db: Session ,scheduleId:int):
    return db.query(ParkModel).filter(ParkModel.id == scheduleId).delete()

def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
def getAdmins(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
    return db.query(AdminModel).filter(AdminModel.created_at.between(start,end)).order_by(desc(AdminModel.created_at)).all()
def getTicketHistories(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(TicketModel).filter(TicketModel.admin_id == adminId).filter(TicketModel.created_at.between(start,end)).order_by(desc(TicketModel.created_at)).all()
    return db.query(TicketModel).order_by(desc(TicketModel.created_at)).all()
def getNotificationHistories(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(NotificationModel).join(NotificationModel.user_notifications).filter(UserNotification.admin_id == adminId).filter(NotificationModel.created_at.between(start,end)).order_by(desc(NotificationModel.created_at)).all()
    return db.query(NotificationModel).order_by(desc(NotificationModel.created_at)).all()
def getSupportTickets(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(SupportTicketModel).filter(SupportTicketModel.admin_id == adminId).filter(SupportTicketModel.created_at.between(start,end)).order_by(desc(SupportTicketModel.created_at)).all()
    return db.query(SupportTicketModel).order_by(desc(SupportTicketModel.created_at)).all()
# gl accounting
def getGlAccounts(db: Session):
    return db.query(GLAccountModel).order_by(desc(GLAccountModel.created_at)).all()
def getGlAccountById(db: Session,id:int):
    return db.query(GLAccountModel).filter(GLAccountModel.id == id).first()
def deleteGlAccount(db: Session ,id:int):
    return db.query(GLAccountModel).filter(GLAccountModel.id == id).delete()
# journal entries 
def getGlJournals(db: Session):
    return db.query(JournalEntryModel).order_by(desc(JournalEntryModel.created_at)).all()
def getGlJournalById(db: Session,id:int):
    return db.query(JournalEntryModel).filter(JournalEntryModel.id == id).first()
def deleteGlJournal(db: Session ,id:int):
    return db.query(JournalEntryModel).filter(JournalEntryModel.id == id).delete()
# service commission
def getServiceCommissions(db: Session,adminId:int=None):
    if adminId:
        return db.query(CommissionModel).filter(CommissionModel.admin_id == adminId).order_by(desc(CommissionModel.id)).all()
    return db.query(CommissionModel).order_by(desc(CommissionModel.id)).all()
def getServiceCommissionById(db: Session,id:int):
    return db.query(CommissionModel).filter(CommissionModel.id == id).first()
def deleteServiceCommission(db: Session ,id:int):
    return db.query(CommissionModel).filter(CommissionModel.id == id).delete()
def getServiceCommissionByProduct(db: Session,productTypeId:int,adminId:int):
    return db.query(CommissionModel).filter(CommissionModel.admin_id==adminId).filter(CommissionModel.product_type_id==productTypeId).first()
# service providers 
def getServiceProviders(db: Session):
    return db.query(ServiceRateModel).order_by(desc(ServiceRateModel.created_at)).all()
def getServiceProviderById(db: Session,id:int):
    return db.query(ServiceRateModel).filter(ServiceRateModel.id == id).first()
def deleteServiceDiscount(db: Session ,discountId:int):
    deleted = db.query(ServiceRateModel).filter(ServiceRateModel.id == discountId).delete()
    if deleted:
        db.commit()
        return True
    return False
def getServiceProviderByProduct(db: Session,productTypeId:int):
    return db.query(ServiceRateModel).filter(ServiceRateModel.active==True).filter(ServiceRateModel.product_type_id==productTypeId).first()
def disableServiceProviderByProduct(db: Session,productId:int,active:bool,model:ServiceRateModel):
    if model and model.id:
        db.query(ServiceRateModel).filter(ServiceRateModel.product_type_id == productId,ServiceRateModel.id != model.id).update({"active": active})
    db.commit()
    db.refresh(model)
    return model
# products
def getProducts(db: Session):
    return db.query(ProductModel).filter(ProductModel.status == True).all()
def getProductById(db: Session,id:int):
    return db.query(ProductModel).filter(ProductModel.id == id).filter(ProductModel.status == True).first()
def getProductByVas(db: Session,vas:int):
    return db.query(ProductModel).filter(ProductModel.vasType == vas).filter(ProductModel.status == True).first()
def deleteProduct(db: Session ,id:int):
    return db.query(ProductModel).filter(ProductModel.id == id).delete()
# billers
def getProductBillers(db: Session):
    return db.query(ProductTypeModel).filter(ProductTypeModel.status == True).order_by(desc(ProductTypeModel.created_at)).all()
def getProductBillersById(db: Session,productId:int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.product_id == productId).filter(ProductTypeModel.status == True).order_by(desc(ProductTypeModel.created_at)).all()
def getProductBillerById(db: Session,id:int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.id == id).filter(ProductTypeModel.status == True).first()
def getProductTypeByProvider(db: Session,provider:str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.provider == provider).filter(ProductTypeModel.status == True).first()
def deleteBiller(db: Session ,id:int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.id == id).delete()
#packages
def getPackages(db: Session):
    return db.query(PackageModel).filter(PackageModel.status == True).order_by(desc(PackageModel.created_at)).all()
def getPackageById(db: Session,id:int):
    return db.query(PackageModel).filter(PackageModel.id == id).filter(PackageModel.status == True).first()
def getPackagesById(db: Session,productTypeId:int):
    return db.query(PackageModel).filter(PackageModel.product_type_id == productTypeId).filter(PackageModel.status == True).order_by(desc(PackageModel.created_at)).all()
def deletePackage(db: Session ,id:int):
    return db.query(PackageModel).filter(PackageModel.id == id).delete()
def getLatestOTP(db: Session,adminId:int,serviceName:str):
    return db.query(OTPModel).filter(OTPModel.admin_id == adminId, OTPModel.servicename == serviceName).order_by(desc(OTPModel.created_at)).first()
def getOTPValue(db: Session,adminId:int,serviceName:str,otp:str):
    return db.query(OTPModel).filter(OTPModel.admin_id == adminId, OTPModel.servicename == serviceName,OTPModel.otp == otp).order_by(desc(OTPModel.created_at)).first()
def totalCashoutTransactionsDaily(db: Session,adminId:int):
    logger.info(f"Started getting daily cashout total for admin {adminId} @ {str(datetime.now())}")
    return db.query(func.sum(CashOutModel.amount)).filter(
    CashOutModel.admin_id == adminId,
    cast(CashOutModel.created_at, Date) == date.today()
).scalar()or 0
def getPaymentByReference(db: Session, reference: str):
    return db.query(PaymentModel).filter(PaymentModel.reference == reference).first()
def getCashoutById(db: Session, cashoutId: int):
    return db.query(CashOutModel).filter(CashOutModel.id == cashoutId).first()
def getPaymentByCashoutId(db: Session, cashoutId: int):
    return db.query(PaymentModel).filter(PaymentModel.cashout_id == cashoutId).first()
# get customer details
def getCustomerById(db: Session, customerId: int):
    return db.query(CustomerModel).filter(CustomerModel.id == customerId).first()
# get ticket details
def getTicketById(db: Session, ticketId: int):
    return db.query(TicketModel).filter(TicketModel.id == ticketId).first()