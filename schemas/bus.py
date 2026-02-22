from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator,model_validator
from schemas.response import BaseResponse
from schemas.route import Route
from schemas.admin import AdminMini
from models.model import BusStatusEnum
from schemas.bus_schedule import BusSchedule


class BusBase(BaseModel):
    name: Union[str, None] = None
    types: Union[str, None] = None
    bus_number:str
    tv: Union[bool, None] = False
    camera: Union[bool, None] = False
    airCondition: Union[bool, None] = False
    billerId: Optional[str]=None
    identifier: Union[str, None] = None
    bus_capacity: Optional[int]=0
    availabilityStatus:Optional[str]=BusStatusEnum.ACTIVE
    provider:Union[AdminMini, None] = None
    @validator("bus_number")
    def bus_number_validator(cls, bus_number:str):
        return bus_number.strip().replace(' ','').upper()
    busImage: Union[str, None] = None
    description: Union[str, None] = None
    base_price: Union[str, None] = None
    admin_id: Optional[int]
    class Config:
        from_attributes = True
        populate_by_name = True
class Bus(BusBase):
    id: Optional[int]=None
    #provider: Optional[Provider]=None
    routes: Optional[List[Route]] = []
    schedules: Optional[List[BusSchedule]] = []
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    @model_validator(mode="after")
    def final_clean(self):
        self.base_price = str(int(int(self.base_price)/100))
        return self
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
    @model_validator(mode="after")
    def final_clean(self):
        self.base_price = str(int(int(self.base_price)/100))
        return self
    class Config:
        from_attributes = True
        populate_by_name = True
class AddBusRequest(BusBase):
    id: Optional[int]=None
    identifier: Optional[int]=None
    schedules:List[dict]
    routes:List[dict]
    @model_validator(mode="before")
    @classmethod
    def compute_kobo(cls, values):
        if values.get("base_price") is not None:
            values["base_price"] = str(int(values["base_price"]) * 100)
        return values
class SwapBusRequest(BaseModel):
    id: int
    swapBusNumber: str
class BusesResponse(BaseResponse):
    data: Union[List[Bus],None] = None    
class BusResponse(BaseResponse):
    data: Bus = None