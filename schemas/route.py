from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.train import Train
from schemas.seat import SeatBase,Seat
from schemas.station import StationBase,Station
from schemas.admin import AdminMini


class RouteBase(BaseModel):
    sourceStation: Union[StationBase, None] = None
    destinationStation: Union[StationBase, None] = None
    identifier: Union[str, None] = None
    provider: Union[AdminMini, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True

class Route(RouteBase):
    sourceStation: Union[Station, None] = None
    destinationStation: Union[Station, None] = None
    identifier: Union[str, None] = None
    provider:AdminMini
    trains:Union[List[Train],None] = []
    prices:Union[List[Seat],None] = []
    created_at: Union[datetime, None] = datetime.now()
    updated_at: Union[datetime, None] = datetime.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class RoutesResponse(BaseResponse):
    data: Union[List[Route],None] = None

class AddRouteRequest(RouteBase):
    id: Optional[int]=None
    admin_id: str
    startId:str
    stopId:str
    seats:Union[List[dict],None]=None
    buses:Union[List[int],None]=None

class RouteResponse(BaseResponse):
    data: Route = None