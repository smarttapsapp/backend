from typing import Optional, Union,List,Dict
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
from schemas.train import TrainBase
from schemas.schedule import ScheduleBase
from schemas.bus_schedule import BusScheduleBase
from schemas.bus import BusBase
from schemas.bus_route import BusRouteBase
from schemas.route import RouteBase


class TicketBase(BaseModel):
    ticket_number: str
    mode:  Union[str, None] = None
    status: str
    booked_at: datetime
    expired_at: datetime

class Ticket(TicketBase):
    id: Optional[int]
    price: Union[str, None] = None
    boarding_date: Union[str, None] = ""
    qr_code: Union[str, None] = None
    schedule: Union[ScheduleBase, None] = None
    busschedule: Union[BusScheduleBase, None] = None
    busName: Union[str, None] = None
    bus_number: Union[str, None] = None
    busImage: Union[str, None] = None
    busPrice: Union[str, None] = None
    seat_label: Union[str, None] = None
    routeName: Union[str, None] = None
    routePrice: Union[str, None] = None
    timeOfOperation: Union[str, None] = None
    arrivalTime: Union[str, None] = None
    departureTime: Union[str, None] = None
    tripPrice: Union[str, None] = None
    tripStatus: Union[str, None] = None
    firstname: Union[str, None] = None
    lastname: Union[str, None] = None
    created_at: Union[datetime, None] = func.now()
    class Config:
        from_attributes = True
        populate_by_name = True

class TicketsResponse(BaseResponse):
    data: Union[List[Ticket],None] = None
    
class TicketResponse(BaseResponse):
    data: Ticket = None