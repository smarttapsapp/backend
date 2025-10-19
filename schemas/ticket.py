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
    mode: str
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
    bus: Union[BusBase, None] = None
    train: Union[TrainBase, None] = None
    route: Union[RouteBase, None] = None
    busroute: Union[BusRouteBase, None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class TicketsResponse(BaseResponse):
    data: Union[List[Ticket],None] = None
    
class TicketResponse(BaseResponse):
    data: Ticket = None