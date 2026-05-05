from decimal import Decimal
from sqlalchemy import func
from datetime import datetime
from typing import Optional, Union,List
from schemas.response import BaseResponse
from pydantic import BaseModel,model_validator,computed_field


class BusScheduleBase(BaseModel):
    timeOfOperation: Union[str, None] = None
    departureTime: Union[str, None] = None
    arrivalTime: Union[str, None] = None
    price: Union[str, None] = "0"
    status:str
    trip_Date:datetime
    identifier: Union[str, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True
class BusSchedule(BusScheduleBase):    
    daysOfOperation: Union[str, None] = None
    companyName: str
    total_seats:int
    booked_seats:int
    busName: Union[str, None] = None
    routeName: Union[str, None] = None
    id: Optional[int]
    @model_validator(mode="after")
    def final_clean(self):
        self.price = str(int(int(self.price)/100))
        return self
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class MobileBusSchedule(BaseModel):  
    timeOfOperation: Union[str, None] = None
    departureTime: Union[str, None] = None
    arrivalTime: Union[str, None] = None
    price: Union[str, None] = "0"
    status:str
    trip_Date:datetime
    identifier: Union[str, None] = None  
    daysOfOperation: Union[str, None] = None
    total_seats:int
    booked_seats:int
    companyName: str
    busName:str
    busID:int
    busNumber:str
    busPrice:str
    camera: Union[bool, None] = False
    tv: Union[bool, None] = False
    airCondition: Union[bool, None] = False
    busImage: Union[str, None] = None
    busDescription: Union[str, None] = None
    routeName:str
    routeId:int
    routePrice:str
    id: Optional[int]
    @computed_field(return_type=Decimal, description="Amount in NGN ₦")
    @property
    def amount_naira(self) -> Decimal:
        return Decimal(int(self.price)+int(self.routePrice)+int(self.busPrice)) / Decimal(100)
    class Config:
        from_attributes = True
        populate_by_name = True
class AddBusScheduleRequest(BusScheduleBase):
    id: Optional[int]=None
    admin_id: int
    bus_route_id: int
    bus_id: int
    mode:str
class BusSchedulesResponse(BaseResponse):
    data: Union[List[BusSchedule],None] = [] 
class BusScheduleResponse(BaseResponse):
    data: BusSchedule = None
class BusSchedulesMobileResponse(BaseResponse):
    data: Union[List[MobileBusSchedule],None] = []
