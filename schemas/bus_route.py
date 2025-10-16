from typing import Optional, Union,List
from datetime import datetime
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.bus import Bus
from schemas.station import Station
from schemas.admin import AdminMini


class BusRouteBase(BaseModel):
    routeName: Union[str, None] = None
    baseprice: Union[str, None] = None
class BusRoute(BusRouteBase):
    sourceStation: Union[Station, None] = None
    destinationStation: Union[Station, None] = None
    identifier: Union[str, None] = None
    id: Optional[int]
    bus:Union[Bus,None] = []
    provider:AdminMini
    created_at: Union[datetime, None] = datetime.now()
    updated_at: Union[datetime, None] = datetime.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class Route(BaseModel):
    baseprice: Union[str, None] = None
    sourceStation: Union[Station, None] = None
    destinationStation: Union[Station, None] = None
    identifier: Union[str, None] = None
    bus:Union[Bus,None] = []
    id: Optional[int]
    provider:AdminMini

    class Config:
        from_attributes = True
        populate_by_name = True

class BusRoutesResponse(BaseResponse):
    data: Union[List[Route],None] = None

class AddBusRouteRequest(BusRouteBase):
    id: Optional[int]=None
    admin_id: int
    startId:int
    stopId:int
    buses:Union[List[int],None]=None

class BusRouteResponse(BaseResponse):
    data: BusRoute = None