from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class ScheduleBase(BaseModel):
    departureTime: Union[str, None] = None
    arrivalTime: Union[str, None] = None


class ScheduleRequest(ScheduleBase):
    user: Union[List[str], None] = None

class Schedule(ScheduleBase):    
    timeOfOperation: Union[str, None] = None
    daysOfOperation: Union[str, None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class SchedulesResponse(BaseResponse):
    data: Union[List[Schedule],None] = None
    
class ScheduleResponse(BaseResponse):
    data: Schedule = None