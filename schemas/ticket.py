from typing import Optional, Union,List,Dict
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
from schemas.train import Train
from schemas.schedule import Schedule
from schemas.bus_schedule import BusSchedule
from schemas.bus import Bus
from schemas.bus_route import BusRoute
from schemas.route import Route
from utils import util


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
    schedule: Union[Schedule, None] = None
    busschedule: Union[BusSchedule, None] = None
    bus: Union[Bus, None] = None
    train: Union[Train, None] = None
    route: Union[Route, None] = None
    busroute: Union[BusRoute, None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class TicketsResponse(BaseResponse):
    data: Union[List[Ticket],None] = None
    
class TicketResponse(BaseResponse):
    data: Ticket = None