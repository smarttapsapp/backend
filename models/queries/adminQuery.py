from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update,case
from models.model import *
import logging

logger = logging.getLogger(__name__)

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
def getAllRole(db: Session,adminId:int=None):
    return db.query(RoleModel).order_by(desc(RoleModel.created_at)).all()
def getRole(db: Session,roleId:int=None):
    return db.query(RoleModel).filter(RoleModel.id ==roleId).first()
def getAllAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).order_by(desc(AdminModel.created_at)).all()
def getAdmin(db: Session,adminId:int=None):
    return db.query(AdminModel).filter(AdminModel.id ==adminId).first()
# trains
def getTrains(db: Session,adminId:int=None):
    if adminId:
        return db.query(TrainModel).filter(TrainModel.admin_id ==adminId).order_by(desc(TrainModel.created_at)).all()
    return db.query(TrainModel).order_by(desc(TrainModel.created_at)).all()
def getTrain(db: Session,busNumber:str):
    return db.query(TrainModel).filter(TrainModel.trainNumber==busNumber).first()
def deleteTrain(db: Session,id:int):
    return db.query(TrainModel).filter(TrainModel.id ==id).delete()
def countTrains(db: Session):
    return db.query(TrainModel).count()
def getTrainsByBusiness(db: Session,adminId:int=None):
    return db.query(TrainModel).filter(TrainModel.route_id ==adminId).order_by(desc(TrainModel.created_at)).all()
#buses
def getBuses(db: Session,adminId:int=None):
    if adminId:
        return db.query(BusModel).filter(BusModel.admin_id ==adminId).order_by(desc(BusModel.created_at)).all()
    return db.query(BusModel).order_by(desc(BusModel.created_at)).all()
def getBus(db: Session,busNumber:str):
    return db.query(BusModel).filter(BusModel.bus_number ==busNumber).first()
def deleteBus(db: Session,id:int):
    return db.query(BusModel).filter(BusModel.id ==id).delete()
def countBuses(db: Session):
    return db.query(BusModel).count()
def getBusesByBusiness(db: Session,parkId:int=None):
    return db.query(BusModel).filter(BusModel.park_id ==parkId).order_by(desc(BusModel.created_at)).all()
# stations
def getstations(db: Session,adminId:int=None):
    if adminId:
        return db.query(StationModel).filter(StationModel.admin_id ==adminId).order_by(desc(StationModel.created_at)).all()
    return db.query(StationModel).all()
def getStationById(db: Session,stationId:int):
    return db.query(StationModel).filter(StationModel.id == stationId).first()
def deleteStation(db: Session ,stationId:int):
    return db.query(StationModel).filter(StationModel.id == stationId).delete()
# routes
def getRoutes(db: Session,adminId:int=None):
    if adminId:
        return db.query(RouteModel).filter(RouteModel.admin_id ==adminId).order_by(desc(RouteModel.created_at)).all()
    return db.query(RouteModel).all()
def getRouteById(db: Session,routeId:int):
    return db.query(RouteModel).filter(RouteModel.id == routeId).first()
def getRouteByStartStopStation(db: Session,start:int,stop:int,adminId:int):
    return db.query(RouteModel).filter(RouteModel.admin_id == adminId).filter(RouteModel.sourceStation_id == start).filter(RouteModel.destinationStation_id == stop).first()
def getRoutesByIds(db:Session,ids:list[int],adminId:int=None):
    if adminId:
        return db.query(RouteModel).filter(RouteModel.admin_id ==adminId).filter(RouteModel.id.in_(ids)).all()
    return db.query(RouteModel).filter(RouteModel.id.in_(ids)).all()
def deleteRoute(db: Session ,routeId:int):
    return db.query(RouteModel).filter(RouteModel.id == routeId).delete()
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
    return db.query(ScheduleModel).filter(ScheduleModel.id == scheduleId).delete()

def getParks(db: Session,startDate:str,endDate:str,adminId:int=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(ParkModel).filter(ParkModel.created_at.between(start,end)).order_by(desc(ParkModel.created_at)).all()
    return db.query(ParkModel).order_by(desc(ParkModel.created_at)).all()
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
            return db.query(NotificationModel).filter(NotificationModel.admin_id == adminId).filter(NotificationModel.created_at.between(start,end)).order_by(desc(NotificationModel.created_at)).all()
    return db.query(NotificationModel).order_by(desc(NotificationModel.created_at)).all()
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

def getServiceCommissions(db: Session,adminId:int=None):
    if adminId:
        return db.query(CommissionModel).filter(CommissionModel.admin_id == adminId).order_by(desc(CommissionModel.id)).all()
    return db.query(CommissionModel).order_by(desc(CommissionModel.id)).all()
def deleteServiceCommission(db: Session ,id:int):
    return db.query(CommissionModel).filter(CommissionModel.id == id).delete()
def getServiceCommissionByProduct(db: Session,productTypeId:int,adminId:int):
    return db.query(CommissionModel).filter(CommissionModel.admin_id==adminId).filter(CommissionModel.product_type_id==productTypeId).first()
def getServiceProviders(db: Session):
    return db.query(ServiceRateModel).order_by(desc(ServiceRateModel.created_at)).all()
def deleteServiceProvider(db: Session ,providerId:int):
    return db.query(ServiceRateModel).filter(ServiceRateModel.id == providerId).delete()
def getServiceProviderByProduct(db: Session,productTypeId:int):
    return db.query(ServiceRateModel).filter(ServiceRateModel.active==True).filter(ServiceRateModel.product_type_id==productTypeId).first()