
import logging
from utils import util
from models.model import *
from utils.constant import *
from datetime import datetime
from sqlalchemy.sql import select,update,case
from models.queries import queries,transactionQuery
from schemas.bus_schedule import BusSchedulesMobileResponse,BaseResponse
from schemas.station import StationsMobileResponse
from schemas.payment import BuyTicketRequest
from schemas.ticket import TicketsResponse
from sqlalchemy.orm import Session
from schemas.setting import Setting
from task.tasks import process_bus_payment
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
logger = logging.getLogger(__name__)

class SeatAlreadyBookedException(Exception):
    def __init__(self, booked_seats: list):
        self.booked_seats = booked_seats
        super().__init__(f"The following seats are already booked: {', '.join(booked_seats)}")

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
        if not trip:
            logger.info(f"{payload.walletAccount} trip not found at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Trip not found",)
        if trip.status not in [TripStatusEnum.SCHEDULED,TripStatusEnum.BOARDING]:
            logger.info(f"{payload.walletAccount} trip staus {trip.status} found at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Trip not found or already completed",)
        provider = db.query(AdminModel).filter(AdminModel.id == trip.admin_id).first()
        logger.info(provider.billerId)
        if not provider:
            logger.info(f"{payload.walletAccount} provider not found")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Provider not found",)
        productType = db.query(ProductTypeModel).filter(ProductTypeModel.billerId == provider.billerId,ProductTypeModel.billerType == "transport").first()
        if not productType:
            logger.info(f"{payload.walletAccount} product not found")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="product Type not found",)
        bookings = []
        conflict_seats = []
        totalAmount = 0
        for seat_id in payload.seats:
            exists = db.execute(select(SeatModel.id,SeatModel.seat_label).join(TicketModel, TicketModel.seat_id == SeatModel.id).filter(TicketModel.busschedule_id == payload.tripId,TicketModel.seat_id == seat_id)).first()
            if exists:
                conflict_seats.append(exists.seat_label)
        if conflict_seats:
            raise SeatAlreadyBookedException(booked_seats=conflict_seats)
        logger.info(f"{payload.walletAccount} started booking ticket at {datetime.now()}")
        serviceDiscount = queries.getServiceProviderByProduct(db=db,productTypeId=productType.id)
        if not serviceDiscount:
            logger.info(f"{payload.customerNumber} Service charge not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        logger.info(f"{payload.walletAccount}  {serviceDiscount.admin.companyName}  is configured configured at {datetime.now()}")
        provider_cost = int(int(payload.amount) - int(serviceDiscount.provider_discount_rate)) if serviceDiscount.provider_discount_type == CommissionType.calculated else int(int(payload.amount) * (1- serviceDiscount.provider_discount_rate/100))
        commssionAmount = int(payload.amount) - provider_cost
        debitAccount = db.query(AccountModel).filter(AccountModel.walletAccount == payload.walletAccount).first()
        if not debitAccount:
            logger.info(f"{payload.walletAccount} account not found")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
        if int(debitAccount.availableBalance) < int(payload.amount):
            logger.info(f"{payload.walletAccount} insufficient fund")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND,)
        for seat_id in payload.seats:
            amountPerTicket = int(payload.amount)/len(payload.seats)
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
                price = amountPerTicket,
                qr_code = f"{ticketId}|{trip.bus.bus_number}|{TicketModeEnum.BUS.value}|{payload.walletAccount}",
                status = BookingStatusEnum.CONFIRMED.value,
                boarding_date = trip.trip_Date,
                expired_at = trip.trip_Date,
            )
            logger.info(f"{payload.walletAccount} adding ticket {ticketId} at {datetime.now()}")
            bookings.append(booking)
        trip.booked_seats += len(payload.seats)
        if trip.booked_seats >= trip.total_seats:
            trip.status = "FULL"
        trnxId = util.generateId()
        debitvalues ={"availableBalance":int(debitAccount.availableBalance) - int(payload.amount),"updated_at":datetime.now()}
        db.execute(update(AccountModel).where(AccountModel.id == debitAccount.id).values(**debitvalues).execution_options(synchronize_session="fetch"))
        creditvalues ={"availableBalance":int(provider.wallet.availableBalance) + int(provider_cost),"updated_at":datetime.now()}
        db.execute(update(AccountModel).where(AccountModel.id == provider.wallet.id).values(**creditvalues).execution_options(synchronize_session="fetch"))
        paymentRecord = [PaymentModel(
                        wallet_id = debitAccount.id,
                        user_id = debitAccount.user_id, 
                        amount = int(payload.amount),
                        payment_type = PaymentEnum.DEBIT,
                        reference =trnxId,
                        event = "charge.success",
                        status = "success",
                        channel = ChannelEnum.MOBILE,
                        providerAmount = provider_cost,
                        statusCode = TransactionCodeEnum.PROCESSING,
                        statusDescription = TransactionStatusEnum.PROCESSING,
                        statusMessage =f"{productType.billerType} Purchase",
                        commissionAmount = commssionAmount,
                        transactionreference=trnxId,
                        product_type_id = productType.id,
                        product_id=productType.product_id,
                        provider_code = provider.billerId,
                        recipient=payload.walletAccount,
                        balanceBefore = debitAccount.availableBalance,
                        balanceAfter = debitAccount.availableBalance,
                        created_at =datetime.now(),
                        updated_at = datetime.now()),
                        PaymentModel(
                        wallet_id = provider.wallet.id,
                        admin_id = provider.id, 
                        amount = provider_cost,
                        payment_type = PaymentEnum.CREDIT,
                        reference =util.generateId(),
                        event = "charge.success",
                        status = "success",
                        channel = ChannelEnum.MOBILE,
                        providerAmount = provider_cost,
                        statusCode = TransactionCodeEnum.PROCESSING,
                        statusDescription = TransactionStatusEnum.PROCESSING,
                        statusMessage =f"{productType.billerType} Purchase",
                        commissionAmount = commssionAmount,
                        transactionreference=trnxId,
                        product_type_id = productType.id,product_id=productType.product_id,
                        packageId=package.packageCode if productType.hasPackages and package else None,
                        provider_code = provider.billerId,
                        recipient=payload.walletAccount,
                        balanceBefore = provider.wallet.availableBalance,
                        balanceAfter = provider.wallet.availableBalance,
                        created_at =datetime.now(),
                        updated_at = datetime.now())
                          ]
        db.add_all(bookings)
        db.add_all(paymentRecord)
        db.commit()
        process_bus_payment.delay(transactionReference=trnxId)
        return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":trnxId})
    except SeatAlreadyBookedException as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
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
