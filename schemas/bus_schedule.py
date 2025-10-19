from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class BusScheduleBase(BaseModel):
    timeOfOperation: Union[str, None] = None
    departureTime: Union[str, None] = None
    arrivalTime: Union[str, None] = None
    price: Union[str, None] = "0"
    identifier: Union[str, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True

class BusSchedule(BusScheduleBase):    
    daysOfOperation: Union[str, None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddBusScheduleRequest(BusScheduleBase):
    id: Optional[int]=None
    admin_id: int
    mode:str
class BusSchedulesResponse(BaseResponse):
    data: Union[List[BusSchedule],None] = None
    
class BusScheduleResponse(BaseResponse):
    data: BusSchedule = None