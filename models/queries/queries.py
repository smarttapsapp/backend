from sqlalchemy.orm import Session,aliased
from sqlalchemy import desc
from typing import List
from sqlalchemy.sql import select,update
from models.model import *
from datetime import datetime, timedelta
from schemas.customer import Customer
import logging

logger = logging.getLogger(__name__)
def getBillByVas(db: Session,vasType:str):
    return db.query(ProductModel).filter(ProductModel.vasType == vasType).first()
def customer(db: Session, userId: int):
    return db.query(CustomerModel).filter(CustomerModel.id == userId).first()
def customer_by_email(db: Session, email: str):
    return db.query(CustomerModel).filter(CustomerModel.email == email).first()
def customer_by_username(db: Session, username: str):
    return db.query(CustomerModel).filter(CustomerModel.username == username).first()
def customer_by_phonenumber(db: Session, phonenumber: str):
    return db.query(CustomerModel).filter(CustomerModel.phonenumber == phonenumber).first()
def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
def save_many(db: Session, models: List[object]):
    db.add_all(models)
    db.commit()
    
def updateUserBvn(db: Session, userId: int,bvn:str):
    stmt = (update(CustomerModel)
            .where(CustomerModel.id == userId)
            .values(
                updated_at=datetime.now(),
                bvn= bvn,
                bvn_verified=True
                    )
            .execution_options(synchronize_session="fetch"))
    res = db.execute(statement=stmt)
    db.commit()
    return  res 
def updateUserNiN(db: Session, userId: int,nin:str):
    stmt = (update(CustomerModel)
            .where(CustomerModel.id == userId)
            .values(
                updated_at=datetime.now(),
                nin= nin,
                nin_verified=True
                    )
            .execution_options(synchronize_session="fetch"))
    res = db.execute(statement=stmt)
    db.commit()
    return  res 
def updateUserNextOfKin(db: Session, userId: int,name:str,phone:str,address:str,relationship:str):
    stmt = (update(CustomerModel)
            .where(CustomerModel.id == userId)
            .values(
                updated_at=datetime.now(),
                next_of_kin_name= name,
                next_of_kin_phone= phone,
                next_of_kin_address= address,
                next_of_kin_relationship= relationship,
                is_next_of_kin=True
                    )
            .execution_options(synchronize_session="fetch"))
    res = db.execute(statement=stmt)
    db.commit()
    return  res 
def get_latest_otp_by_servicename(userId:int,servicename: str, db: Session):
    return db.query(OTPModel).filter(OTPModel.user_id==userId,OTPModel.status == "OPEN",OTPModel.servicename == servicename).order_by(desc(OTPModel.id)).first()
def supportTickets(db: Session,userId:int):
    return db.query(SupportTicketModel).filter(SupportTicketModel.user_id==userId).order_by(desc(SupportTicketModel.created_at)).all()
def deleteSupportTickets(db: Session ,userId:int,id:int):
    return db.query(SupportTicketModel).filter(SupportTicketModel.user_id==userId).filter(SupportTicketModel.id == id).delete()

def notifications(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).join(UserNotification).join(CustomerModel).filter(CustomerModel.id==userId).all()
    return db.query(NotificationModel).all()
def notification(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def readNotifications(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def readNotification(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def deleteNotifications(db: Session,userId:int):
    if userId:
        return db.query(NotificationModel).filter(NotificationModel.user_notifications).all()
    return db.query(NotificationModel).first()
def queryNotifications(db: Session ,userId:int):
    return db.query(NotificationModel).join(UserNotification).join(CustomerModel).filter(CustomerModel.id == userId).order_by(desc(NotificationModel.updated_at)).all()
def deleteNotification(db: Session ,userId:int,notificationId:int):
    return db.query(NotificationModel).filter(NotificationModel.id == notificationId).delete()
def queryNotification(db: Session ,userId:int,notificationId:int):
    return db.query(NotificationModel).join(UserNotification).join(CustomerModel).filter(CustomerModel.id == userId).filter(NotificationModel.id == notificationId).order_by(desc(NotificationModel.updated_at)).first()
def update_user_agent_records(db: Session, id: int, user: Customer):
    userRecord = db.query(CustomerModel).filter(CustomerModel.id == id).first()
    if userRecord is None:
        return None
    userRecord.email = user.email
    userRecord.password = user.password
    userRecord.email_verified = user.email_verified
    userRecord.nin_submitted = user.nin_submitted
    userRecord.nin_verified = user.nin_verified
    userRecord.bvn_verified = user.bvn_verified
    userRecord.account_type = user.account_type
    userRecord.account_status = user.account_status
    userRecord.updated_at = datetime.now()
    db.add(userRecord)
    db.commit()
    db.refresh(userRecord)
    return userRecord
def getUserNotificationPreference(db: Session, userId:int):
    return db.query(UserNotificationPreference).filter(UserNotificationPreference.customer_id == userId).first()
def queryWallet(db:Session,walletAccount:str):
    return db.query(AccountModel).filter(AccountModel.walletAccount == walletAccount).first()
def getLastpaymentByAccount(db: Session, accountId: int):
    return db.query(PaymentModel).filter(PaymentModel.wallet_id == accountId).filter(PaymentModel.payment_type == PaymentEnum.DEBIT).order_by(desc(PaymentModel.updated_at)).first()
def getBusProvider(db: Session):
    return db.query(AdminModel).join(AdminModel.role).filter(RoleModel.tag == AdminRoleEnum.BUSPROVIDER).order_by(desc(AdminModel.created_at)).all()
def query_bus_routes_by_provider(db: Session,adminId:int):
    return db.query(RouteModel).filter(RouteModel.admin_id==adminId).filter(RouteModel.mode==MovableEnum.BUS.value).order_by(desc(RouteModel.created_at)).all()
def getTrainProvider(db: Session):
    return db.query(AdminModel).join(AdminModel.role).filter(RoleModel.tag == AdminRoleEnum.TRAINPROVIDER).order_by(desc(AdminModel.created_at)).all()
def query_train_routes_by_provider(db: Session,adminId:int):
    return db.query(RouteModel).filter(RouteModel.admin_id==adminId).filter(RouteModel.mode==MovableEnum.TRAIN.value).order_by(desc(RouteModel.created_at)).all()
def getstations(db: Session):
    return db.query(StationModel).all()
def getstations(db: Session,mode:MovableEnum,adminId:int=None):
    if adminId:
        return db.query(StationModel).filter(StationModel.admin_id == adminId).filter(StationModel.mode == mode.value).all()
    return db.query(StationModel).filter(StationModel.mode == mode.value).all()
def getStationById(db: Session,stationId:int):
    return db.query(StationModel).filter(StationModel.id == stationId).first()
def deleteStation(db: Session ,stationId:int):
    deleted = db.query(StationModel).filter(StationModel.id == stationId).delete()
    if deleted:
        db.commit()
        return True
    return False
def getRoutes(db: Session,adminId:int=None):
    if adminId:
        return db.query(RouteModel).filter(RouteModel.admin_id ==adminId).order_by(desc(RouteModel.created_at)).all()
    return db.query(RouteModel).order_by(desc(RouteModel.created_at)).all()
def getRouteById(db: Session,routeId:int):
    return db.query(RouteModel).filter(RouteModel.id == routeId).first()
def deleteRoute(db: Session ,routeId:int):
    deleted = db.query(RouteModel).filter(RouteModel.id == routeId).delete()
    if deleted:
        db.commit()
        return True
    return False
def query_stations(db: Session,mode:str):
    return db.query(StationModel).filter(StationModel.mode == mode).all()
def queryRouteByIdAndMode(db: Session,routeId:int,mode:str):
    return db.query(RouteModel).filter(RouteModel.id == routeId).filter(RouteModel.mode == mode).first()
def query_routes(db: Session,mode:str):
    return db.query(RouteModel).filter(RouteModel.mode == mode).all()
def query_routes_by_stations(db: Session,departure:str,arrival:str,mode:str):
    SourceStation = aliased(StationModel)
    DestinationStation = aliased(StationModel)
    return (
        db.query(RouteModel)
        .join(SourceStation, RouteModel.sourceStation)
        .join(DestinationStation, RouteModel.destinationStation)
        .filter(RouteModel.mode == mode)
        .filter(func.lower(SourceStation.stationName).like(f"%{departure.lower()}%"))
        .filter(func.lower(DestinationStation.stationName).like(f"%{arrival.lower()}%"))
        .all()
    )
def busById(db: Session,busId:int):
    return db.query(BusModel).filter(BusModel.id == busId).first()
def deleteBus(db: Session ,busId:int):
    deleted = db.query(BusModel).filter(BusModel.id == busId).delete()
    if deleted:
        db.commit()
        return True
    return False
def getPaymentHistories(db: Session,userId:int,startDate:str,endDate:str):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        return db.query(PaymentModel).filter(PaymentModel.user_id == userId).filter(PaymentModel.created_at.between(start,end)).order_by(desc(PaymentModel.created_at)).all()
    return db.query(PaymentModel).filter(PaymentModel.user_id == userId).order_by(desc(PaymentModel.created_at)).all()
def getPaymentHistoriesByTransaction(db: Session,userId:int,startDate:str,endDate:str,transType:str):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        return db.query(PaymentModel).filter(PaymentModel.user_id == userId).filter(PaymentModel.payment_type == transType).filter(PaymentModel.created_at.between(start,end)).order_by(desc(PaymentModel.created_at)).all()
    return db.query(PaymentModel).filter(PaymentModel.payment_type == transType).filter(PaymentModel.user_id == userId).order_by(desc(PaymentModel.created_at)).all()
def getAllPaymentsHistories(db: Session,startDate:str,endDate:str,adminId:str=None):
    logger.info(f'started querying payment for {startDate} {endDate} {adminId}')
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(PaymentModel).filter(PaymentModel.admin_id == adminId).filter(PaymentModel.created_at.between(start,end)).order_by(desc(PaymentModel.created_at)).all()
        return db.query(PaymentModel).filter(PaymentModel.created_at.between(start,end)).order_by(desc(PaymentModel.created_at)).all()    
def getListOfcashout(db: Session,startDate:str,endDate:str,adminId:str=None):
    logger.info(f'started querying payment for {startDate} {endDate} {adminId}')
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if adminId:
            return db.query(CashOutModel).filter(CashOutModel.admin_id == adminId).filter(CashOutModel.created_at.between(start,end)).order_by(desc(CashOutModel.created_at)).all()
        return db.query(CashOutModel).filter(CashOutModel.created_at.between(start,end)).order_by(desc(CashOutModel.created_at)).all()    
def paymentByTransactionNumber(db:Session,mode:PaymentEnum,transactionId:str,userId=int):
    return db.query(PaymentModel).filter(PaymentModel.user_id == userId).filter(PaymentModel.reference == transactionId).filter(PaymentModel.payment_type == mode).first()
def ticketByTicketNumber(db:Session,mode:TicketModeEnum,ticketId:str):
    return db.query(TicketModel).filter(TicketModel.ticket_number == ticketId).filter(TicketModel.mode == mode).first()
def getTicketHistories(db: Session,userId:int,startDate:str=None,endDate:str=None):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        return db.query(TicketModel).filter(TicketModel.customer_id == userId).filter(TicketModel.created_at.between(start,end)).order_by(desc(TicketModel.created_at)).all()
    return db.query(TicketModel).filter(TicketModel.customer_id == userId).order_by(desc(TicketModel.created_at)).all()
def getTicketsHistoriesByTransaction(db: Session,userId:int,startDate:str,endDate:str,transType:str):
    if startDate and endDate:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        return db.query(TicketModel).filter(TicketModel.customer_id == userId).filter(TicketModel.mode == transType).filter(TicketModel.created_at.between(start,end)).order_by(desc(TicketModel.created_at)).all()
    return db.query(TicketModel).filter(TicketModel.mode == transType).filter(TicketModel.customer_id == userId).order_by(desc(TicketModel.created_at)).all()
def getRoleByTag(db: Session,tag:str):
    return db.query(RoleModel).filter(RoleModel.tag == tag).first()
def getRoleById(db: Session,roleId:int):
    return db.query(RoleModel).filter(RoleModel.id == roleId).first()
def deleteRole(db: Session ,roleId:int):
    return db.query(RoleModel).filter(RoleModel.id == roleId).delete()
def getParks(db: Session):
    return db.query(ParkModel).all()
def getParkById(db: Session,parkId:int):
    return db.query(ParkModel).filter(ParkModel.id == parkId).first()
def deletePark(db: Session ,parkId:int):
    return db.query(ParkModel).filter(ParkModel.id == parkId).delete()
def getProductTypeBYname(db: Session,name:str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerType == name).first()
def getDailyCashoutTransactionsByUser(db: Session,productId:int,userId:int):
    logger.info(f"Started getting daily cashout total for user {userId} @ {str(datetime.now())}")
    return db.query(func.sum(CashOutModel.amount)).filter(CashOutModel.user_id == userId).scalar()