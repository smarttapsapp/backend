from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.train import Train
from schemas.bus import Bus
from schemas.station import Station


class RouteBase(BaseModel):
    routeName: Union[str, None] = None


class RouteRequest(RouteBase):
    user: Union[List[str], None] = None

class Route(RouteBase):
    sourceStation: Union[Station, None] = None
    destinationStation: Union[Station, None] = None
    trains:Union[List[Train],None] = None
    buses:Union[List[Bus],None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class RoutesResponse(BaseResponse):
    data: Union[List[Route],None] = None
    
class RouteResponse(BaseResponse):
    data: Route = None