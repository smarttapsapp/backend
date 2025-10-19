from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.seat import Seat
from schemas.admin import AdminMini
from schemas.schedule import Schedule
#from schemas.route import Route


class TrainBase(BaseModel):
    trainName: Union[str, None] = None
    trainNumber: Union[str, None] = None
    image: Union[str, None] = None
    description: Union[str, None] = None
    admin_id: Optional[int]
    provider:AdminMini
    billerId: Optional[str]=None
    class Config:
        from_attributes = True
        populate_by_name = True

class Train(TrainBase):
    schedules: Union[List[Schedule],None] = None
    id: Optional[int]
    provider:AdminMini
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddTrainRequest(TrainBase):
    id: Optional[int] = None
    schedules:List[dict]
    routes:List[int]

class TrainsResponse(BaseResponse):
    data: Union[List[Train],None] = None
    
class TrainResponse(BaseResponse):
    data: Train = None