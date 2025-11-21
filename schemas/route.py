from typing import Optional, Union,List
from datetime import datetime
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.station import StationBase,Station
from schemas.admin import AdminMini
from schemas.train import Train
from schemas.seat import Seat
from pydantic import BaseModel,model_validator


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
    baseprice: Union[str, None] = 0
    #trains:Union[List[Train],None] = []
    #prices:Union[List[Seat],None] = []
    created_at: Union[datetime, None] = datetime.now()
    updated_at: Union[datetime, None] = datetime.now()
    @model_validator(mode="after")
    def final_clean(self):
        self.baseprice = str(int(int(self.baseprice)/100))
        return self

    class Config:
        from_attributes = True
        populate_by_name = True
class TrainRoute(RouteBase):
    sourceStation: Union[Station, None] = None
    destinationStation: Union[Station, None] = None
    identifier: Union[str, None] = None
    provider:AdminMini
    baseprice: Union[str, None] = 0
    trains:Union[List[Train],None] = []
    prices:Union[List[Seat],None] = []
    created_at: Union[datetime, None] = datetime.now()
    updated_at: Union[datetime, None] = datetime.now()
    @model_validator(mode="after")
    def final_clean(self):
        self.baseprice = str(int(int(self.baseprice)/100))
        return self

    class Config:
        from_attributes = True
        populate_by_name = True

class RoutesResponse(BaseResponse):
    data: Union[List[Route],None] = None

class AddRouteRequest(RouteBase):
    identifier: Union[str, None] = None
    id: Optional[int]=None
    admin_id: str
    startId:str
    stopId:str
    prices:Union[List[dict],None]=None
    buses:Union[List[int],None]=None

class RouteResponse(BaseResponse):
    data: Route = None
class TrainRoutesResponse(BaseResponse):
    data: Union[List[TrainRoute],None] = None
class TrainRouteResponse(BaseResponse):
    data: TrainRoute = None