
import logging
from utils import util
from models.model import *
from utils.constant import *
from datetime import datetime
from models.queries import queries,transactionQuery
from schemas.bus_schedule import BusSchedulesMobileResponse,BaseResponse
from schemas.station import StationsMobileResponse
from schemas.payment import BuyTicketRequest
from schemas.ticket import TicketsResponse
from sqlalchemy.orm import Session
from schemas.setting import Setting
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
logger = logging.getLogger(__name__)

def stations(response: Response,db: Session):
    try:
        logger.info(f"Started getting bus stations")
        return StationsMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=queries.query_stations(db=db,mode="bus"))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return StationsMobileResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,data=[])
async def searchMovablesRoutes(response: Response,db: Session,latitude:str,longitude:str,departure: str=None,arrival: str=None):
    try:
        logger.info(f"Started searching for bus route at {datetime.now()}")
        data = []
        message = None
        if departure and arrival:
            logger.info(f"Searching for bus trip from {departure} to {arrival}")
            route = queries.getBusRoutesByStations(db=db,departure=departure,arrival=arrival)
        elif departure and arrival:
            route = queries.getBusRoutesByStations(db=db,departure=departure)
        elif arrival and departure:
            route = queries.getBusRoutesByStations(db=db,arrival=arrival)
        else:
            route = queries.getBusRoutesByStations(db=db)
        if route:
            return BusSchedulesMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=route,message=message)
        else:
            message = f"No bus route found from {departure} to {arrival}. Enter a new route or select from options" if departure and arrival else f"No bus route found. Enter a new route or select from options"
        if longitude and latitude:
            data = queries.getAdminRoutes(db=db,role=AdminRoleEnum.BUSPROVIDER,latitude=float(latitude),longitude=float(longitude),radius_km=20)
            if data:
                return BusSchedulesMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data,message=message)
        data = queries.query_routes(db=db,mode=mode)
        return BusSchedulesMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data,message=message)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusSchedulesMobileResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getBusSeat(response: Response,db: Session,busId:int):
    try:
        logger.info(f"Started searching for bus seat at {datetime.now()}")
        data = []
        message = None
        if departure and arrival:
            logger.info(f"Searching for bus trip from {departure} to {arrival}")
            route = queries.getBusRoutesByStations(db=db,departure=departure,arrival=arrival)
        elif departure and arrival:
            route = queries.getBusRoutesByStations(db=db,departure=departure)
        elif arrival and departure:
            route = queries.getBusRoutesByStations(db=db,arrival=arrival)
        else:
            route = queries.getBusRoutesByStations(db=db)
        if route:
            return BusSchedulesMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=route,message=message)
        else:
            message = f"No bus route found from {departure} to {arrival}. Enter a new route or select from options" if departure and arrival else f"No bus route found. Enter a new route or select from options"
        if longitude and latitude:
            data = queries.getAdminRoutes(db=db,role=AdminRoleEnum.BUSPROVIDER,latitude=float(latitude),longitude=float(longitude),radius_km=20)
            if data:
                return BusSchedulesMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data,message=message)
        data = queries.query_routes(db=db,mode=mode)
        return BusSchedulesMobileResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data,message=message)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BusSchedulesMobileResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def get_trip_seats(response: Response, tripId: int, db: Session):
    try:
        trip = db.query(BusScheduleModel).filter(
            BusScheduleModel.id == tripId
        ).first()

        if not trip:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(
                statusCode="404",
                statusDescription="Trip not found",
                data=[]
            )

        if not trip.bus:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode="400",
                statusDescription="Bus not assigned",
                data=[]
            )

        seats = db.query(SeatModel).filter(
            SeatModel.bus_type_id == trip.bus.bus_type_id
        ).all()

        booked = db.query(TicketModel.seat_id).filter(
            TicketModel.busschedule_id == tripId,
            TicketModel.status.in_([
                BookingStatusEnum.CONFIRMED,
                BookingStatusEnum.BOARDED
            ])
        ).all()

        booked_ids = {b[0] for b in booked}

        result = []

        for seat in seats:
            if seat.seattype != SeatTypeEnum.PASSENGER:
                result.append({
                    "id": seat.id,
                    "label": seat.seat_label,
                    "row": seat.seatrow,
                    "column": seat.seatcolumn,
                    "type": seat.seattype,
                    "isBookable":seat.is_bookable,
                    "status": seat.seattype
                })
                continue 
            result.append({
                "id": seat.id,
                "label": seat.seat_label,
                "row": seat.seatrow,
                "column": seat.seatcolumn,
                "type": seat.seattype,
                "isBookable":seat.is_bookable,
                "status": "BOOKED" if seat.id in booked_ids else "AVAILABLE"
            })

        response.status_code = status.HTTP_200_OK

        return BaseResponse(
            statusCode="00",
            statusDescription="Successful",
            data=result
        )

    except Exception as ex:
        print(str(ex))
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(
            statusCode="500",
            statusDescription=SYSTEMBUSY,
            data=[]
        )
async def confirm_booking(db:Session,request:Request,response:Response,setting:Setting,payload:BuyTicketRequest,user:CustomerModel,background_task:BackgroundTasks):
    try:
        trip = db.query(BusScheduleModel).filter(BusScheduleModel.id == payload.tripId).with_for_update().first()
        if trip:
            bookings = []
            for seat_id in payload.seats:
                exists = db.query(TicketModel).filter(TicketModel.busschedule_id == payload.tripId,TicketModel.seat_id == seat_id).first()
                if exists:
                    raise Exception("Seat already booked")
                ticketId = f"BUS-{util.generateId()}"
                booking = TicketModel(
                    busschedule_id=trip.id,
                    customer_id = user.id,
                    seat_id = seat_id,
                    admin_id = trip.admin_id,
                    bus_id = trip.bus_id,
                    busroute_id =trip.bus_route_id,
                    ticket_number = f"BUS-{util.generateId()}",
                    isdelete = False,
                    price = payload.amount,
                    qr_code = f"{ticketId}|{trip.bus.bus_number}|{TicketModeEnum.BUS.value}|{payload.walletAccount}",
                    status = BookingStatusEnum.CONFIRMED.value,
                    boarding_date = trip.trip_Date,
                    expired_at = trip.trip_Date,
                )

                db.add(booking)
                bookings.append(booking)

            trip.booked_seats += len(payload.seats)

            if trip.booked_seats >= trip.total_seats:
                trip.status = "FULL"

            db.commit()
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Trip not found or already completed",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getAllTickets(response: Response,db: Session,user: CustomerModel,startDate: str=None,endDate: str=None,transactionType: str=None):
    try:
        logger.info(f"started querying payments from {startDate} to {endDate} for {transactionType}" )
        data = transactionQuery.getTickets(db=db,userId=user.id,startDate=startDate,endDate=endDate,transType=transactionType)
        return TicketsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,data=[])
async def debitBusTicket(db:Session,request:Request,response:Response,setting:Setting,payload:BuyTicketRequest,user:CustomerModel,background_task:BackgroundTasks):
    try:
        logger.info(f"Started debit process for bus ticket payment {payload.busId} for amount {payload.amount} for {user.firstname}")
        if user.wallet.walletAccount == payload.walletAccount:
            bus = queries.busById(db=db,busId=payload.busId)
            if bus:
                if bus.availabilityStatus in [BusStatusEnum.BOARDING,BusStatusEnum.ACTIVE,BusStatusEnum.OPEN]:
                    product = adminQuery.getBillerByBillerId(db=db,billerId=bus.billerId)
                    if product:
                        if int(user.wallet.availableBalance) > int(payload.amount):
                            logger.info(f"balance is sufficient {user.wallet.availableBalance}")
                            route = queries.getBusRouteByIdentifier(db=db, routeId=payload.routeId)
                            if route:
                                merchant = adminQuery.getAdminByCustomerId(db=db,id=user.id)
                                return await glAccountingService.debitBusTransaction(request=request,response=response,setting=setting,db=db,biller=product,customer=user,payload=payload,bus=bus,route=route,background_task=background_task,remark=f"{bus.name}/{payload.busId}",merchant=merchant)
                            else:
                                logger.info(f"{ROUTEERROR} with user {user.firstname}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ROUTEERROR)
                        else:
                            logger.info(f"{INSUFFICIENTFUND} with user {user.firstname}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
                    else:
                        logger.info(f"Invalid bus selected {payload.busId} for {user.firstname}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus error biller not found")
                else:
                    logger.info(f"Bus {payload.busId} is not available for {user.firstname}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus currently not available at the moment")
            else:
                logger.info(f"Invalid bus selected {payload.busId} for {user.firstname}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus not found")
        else:
            logger.info(f"Invalid account selected {payload.walletAccount} for {user.firstname}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
