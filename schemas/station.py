from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse

class StationBase(BaseModel):
    stationName: Union[str, None] = None
    location: Union[str, None] = None
    admin_id: int
    mode: Union[str, None] = None

class Station(StationBase):
    identifier: Union[str, None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class StationsResponse(BaseResponse):
    data: Union[List[Station],None] = None
    
class StationResponse(BaseResponse):
    data: Station = None

class AddStationRequest(StationBase):
    identifier: Optional[str]=None