from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.seat import Seat


class ScheduleBase(BaseModel):
    timeOfOperation: Union[str, None] = None
    departureTime: Union[str, None] = None
    arrivalTime: Union[str, None] = None
    identifier: Union[str, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True



class Schedule(ScheduleBase):    
    seats: Union[List[Seat],None] = None
    daysOfOperation: Union[str, None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddScheduleRequest(ScheduleBase):
    id: Optional[int]=None
    admin_id: int
    mode:str
class SchedulesResponse(BaseResponse):
    data: Union[List[Schedule],None] = None
    
class ScheduleResponse(BaseResponse):
    data: Schedule = None