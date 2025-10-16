from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
#from schemas.bus_route import BusRoute
from schemas.bus_schedule import BusSchedule


class BusBase(BaseModel):
    name: Union[str, None] = None
    types: Union[str, None] = None
    bus_number:str
    tv: Union[bool, None] = False
    camera: Union[bool, None] = False
    airCondition: Union[bool, None] = False
    @validator("bus_number")
    def bus_number_validator(cls, bus_number:str):
        return bus_number.strip().replace(' ','').upper()
    busImage: Union[str, None] = None
    description: Union[str, None] = None
    base_price: Union[str, None] = None
class Bus(BusBase):
    id: Optional[int]=None
    billerId: Optional[str]=None
    identifier: Union[str, None] = None
    #provider: Optional[Provider]=None
    schedules: Optional[List[BusSchedule]] = []
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()
    class Config:
        from_attributes = True
        populate_by_name = True

class MiniBus(BaseModel):
    name: Union[str, None] = None
    types: Union[str, None] = None
    bus_number:str
    tv: Union[bool, None] = False
    camera: Union[bool, None] = False
    airCondition: Union[bool, None] = False
    @validator("bus_number")
    def bus_number_validator(cls, bus_number:str):
        return bus_number.strip().replace(' ','').upper()
    busImage: Union[str, None] = None
    description: Union[str, None] = None
    base_price: Union[str, None] = None
    id: Optional[int]=None
    billerId: Optional[str]=None
    identifier: Union[str, None] = None
    schedules: Optional[List[BusSchedule]] = []
    class Config:
        from_attributes = True
        populate_by_name = True
class AddBusRequest(BusBase):
    #busschedules:List[int]
    schedules:List[dict]
    routes:List[dict]
class BusesResponse(BaseResponse):
    data: Union[List[Bus],None] = None    
class BusResponse(BaseResponse):
    data: Bus = None