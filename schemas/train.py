from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.seat import Seat
from schemas.schedule import Schedule


class TrainBase(BaseModel):
    trainName: Union[str, None] = None
    trainNumber: Union[str, None] = None


class TrainRequest(TrainBase):
    user: Union[List[str], None] = None

class Train(TrainBase):
    schedules: Union[List[Schedule],None] = None
    seats: Union[List[Seat],None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class TrainsResponse(BaseResponse):
    data: Union[List[Train],None] = None
    
class TrainResponse(BaseResponse):
    data: Train = None