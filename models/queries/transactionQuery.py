
from sqlalchemy.orm import Session
from sqlalchemy.sql import select,update,case
from models.model import *
import logging

logger = logging.getLogger(__name__)

def getAll(db: Session):
    return db.query(TransactionModel).all()

def getAllByUser(db: Session, userId:int,start:DateTime,end:DateTime,transType:str):
    return db.query(TransactionModel).filter(TransactionModel.user_id==userId).all()

def getOne(db: Session, id: int):
    return db.query(TransactionModel).first()

def getOneById(db: Session, id: int):
    return db.query(TransactionModel).filter(TransactionModel.id == id).first()
def getTickets(db: Session,userId:int,startDate:str=None,endDate:str=None,transType:str=None):
    if startDate and endDate and transType:
        start = datetime.strptime(startDate, "%Y-%m-%d").date()
        end = datetime.strptime(endDate, "%Y-%m-%d").date()+ timedelta(days=1) - timedelta(seconds=1)
        if transType.lower() == "bus":
            return (db.execute(select(
                TicketModel.id,
                TicketModel.ticket_number,
                TicketModel.price,
                TicketModel.status,
                TicketModel.qr_code,
                TicketModel.boarding_date,
                TicketModel.mode,
                TicketModel.expired_at,
                TicketModel.booked_at, 
                TicketModel.created_at, 
                BusModel.name.label("busName"),
                BusModel.bus_number,
                BusModel.busImage,
                BusModel.base_price.label("busPrice"),
                SeatModel.seat_label,
                BusRouteModel.routeName,
                BusRouteModel.baseprice.label("routePrice"),
                BusScheduleModel.timeOfOperation,
                BusScheduleModel.arrivalTime,
                BusScheduleModel.departureTime,
                BusScheduleModel.status.label("tripStatus"),
                BusScheduleModel.price.label("tripPrice"),
                CustomerModel.firstname,
                CustomerModel.lastname)
                .join(CustomerModel, CustomerModel.id == TicketModel.customer_id)
                .join(BusModel, BusModel.id == TicketModel.bus_id)
                .join(BusRouteModel, BusRouteModel.id == TicketModel.busroute_id)
                .join(BusScheduleModel, BusScheduleModel.id == TicketModel.busschedule_id)
                .join(SeatModel, SeatModel.id == TicketModel.seat_id)
                .filter(TicketModel.customer_id == userId,TicketModel.mode == transType,TicketModel.isdelete == False))
                .filter(TicketModel.created_at.between(start,end)).mappings().all())
        else:
            return (db.execute(select(
                TicketModel.id,
                TicketModel.ticket_number,
                TicketModel.price,
                TicketModel.status,
                TicketModel.qr_code,
                TicketModel.boarding_date,
                TicketModel.mode,
                TicketModel.expired_at,
                TicketModel.booked_at, 
                TicketModel.created_at, 
                TrainModel.trainName,
                TrainModel.trainNumber,
                TrainModel.image,
                SeatModel.seat_label,
                RouteModel.routeName,
                RouteModel.baseprice.label("routePrice"),
                ScheduleModel.timeOfOperation,
                ScheduleModel.arrivalTime,
                ScheduleModel.departureTime,
                ScheduleModel.status.label("tripStatus"),
                ScheduleModel.price.label("tripPrice"),
                CustomerModel.firstname,
                CustomerModel.lastname)
                .join(CustomerModel, CustomerModel.id == TicketModel.customer_id)
                .join(TrainModel, TrainModel.id == TicketModel.train_id)
                .join(RouteModel, BusRouteModel.id == TicketModel.route_id)
                .join(ScheduleModel, ScheduleModel.id == TicketModel.schedule_id)
                .join(SeatModel, SeatModel.id == TicketModel.seat_id)
                .filter(TicketModel.customer_id == userId,TicketModel.mode == transType,TicketModel.isdelete == False))
                .filter(TicketModel.created_at.between(start,end)).mappings().all())
    else:
        if transType.lower() == "bus":
            return (db.execute(select(
        TicketModel.id,
        TicketModel.ticket_number,
        TicketModel.price,
        TicketModel.status,
        TicketModel.qr_code,
        TicketModel.boarding_date,
        TicketModel.mode,
        TicketModel.booked_at, 
        TicketModel.expired_at,
        TicketModel.created_at, 
        BusModel.name.label("busName"),
        BusModel.bus_number,
        BusModel.busImage,
        BusModel.base_price.label("busPrice"),
        SeatModel.seat_label,
        BusRouteModel.routeName,
        BusRouteModel.baseprice.label("routePrice"),
        BusScheduleModel.timeOfOperation,
        BusScheduleModel.arrivalTime,
        BusScheduleModel.departureTime,
        BusScheduleModel.status.label("tripStatus"),
        BusScheduleModel.price.label("tripPrice"),
        CustomerModel.firstname,
        CustomerModel.lastname)
        .join(CustomerModel, CustomerModel.id == TicketModel.customer_id)
        .join(BusModel, BusModel.id == TicketModel.bus_id)
        .join(BusRouteModel, BusRouteModel.id == TicketModel.busroute_id)
        .join(BusScheduleModel, BusScheduleModel.id == TicketModel.busschedule_id)
        .join(SeatModel, SeatModel.id == TicketModel.seat_id)
        .filter(TicketModel.customer_id == userId,TicketModel.mode == transType,TicketModel.isdelete == False)).mappings().all())