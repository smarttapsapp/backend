from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
from schemas.park import Park
from schemas.schedule import Schedule


class BusBase(BaseModel):
    name: Union[str, None] = None
    seatCount: Union[int, None] = None
    types: Union[str, None] = None
    bus_number:str
    @validator("bus_number")
    def bus_number_validator(cls, bus_number:str):
        return bus_number.strip().replace(' ','').upper()
    busImage: Union[str, None] = None
    description: Union[str, None] = None
    base_price: Union[str, None] = None


class BusRequest(BusBase):
    user: Union[List[str], None] = None

class Bus(BusBase):
    tv: Union[bool, None] = False
    camera: Union[bool, None] = False
    airCondition: Union[bool, None] = False
    id: Optional[int]=None
    park: Optional[Park]=None
    schedules: Optional[List[Schedule]] = []
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddBusRequest(Bus):
    busschedules:List[int]
    busroutes:List[int]
class BusesResponse(BaseResponse):
    data: Union[List[Bus],None] = None
    
class BusResponse(BaseResponse):
    data: Bus = None