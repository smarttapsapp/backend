from typing import Optional, Union,List
from datetime import datetime
from pydantic import BaseModel, validator
from schemas.response import BaseResponse
from schemas.bus import Bus
from schemas.station import Station,StationBase
from schemas.admin import AdminMini

class BusRouteBase(BaseModel):
    sourceStation: Union[StationBase, None] = None
    destinationStation: Union[StationBase, None] = None
    identifier: Union[str, None] = None
    provider:Union[AdminMini, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True
class BusRoute(BaseModel):
    sourceStation: Union[Station, None] = None
    destinationStation: Union[Station, None] = None
    identifier: Union[str, None] = None
    provider: Union[AdminMini, None] = None 
    routeName: Union[str, None] = None
    baseprice: Union[str, None] = None
    id: Optional[int]
    bus:Union[Bus,None] = []
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
    routeName: Union[str, None] = None
    provider: Union[AdminMini, None] = None 
    @validator("baseprice")
    def baseprice_validator(cls, baseprice):
        return str(int(int(baseprice)/100))

    class Config:
        from_attributes = True
        populate_by_name = True

class BusRoutesResponse(BaseResponse):
    message: Union[str,None] = None
    data: Union[List[Route],None] = None

class AddBusRouteRequest(BusRouteBase):
    id: Optional[int]=None
    admin_id: int
    startId:int
    stopId:int
    baseprice:Optional[str]=0
    buses:Union[List[int],None]=None

class BusRouteResponse(BaseResponse):
    data: BusRoute = None