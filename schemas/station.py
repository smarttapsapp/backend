from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse

class StationMobile(BaseModel):
    stationName: Union[str, None] = None
    location: Union[str, None] = None
    mode: Union[str, None] = None
    identifier: Union[str, None] = None
    parkImage: Optional[str]=None
    companyName: Union[str, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True

class StationBase(BaseModel):
    admin_id: int
    stationName: Union[str, None] = None
    location: Union[str, None] = None
    mode: Union[str, None] = None
    identifier: Union[str, None] = None
    contact: Optional[str]=None
    address: Optional[str]=None
    parkImage: Optional[str]=None
    description: Optional[str]=None
    status:Optional[bool]=True
    class Config:
        from_attributes = True
        populate_by_name = True

class Station(StationBase):
    companyName: Union[str, None] = None
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
    id: Optional[str]=None

class StationsMobileResponse(BaseResponse):
    data: Union[List[StationMobile],None] = None