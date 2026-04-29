from typing import Optional, Union,List
from datetime import datetime
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.bus_seat import SeatCreate

class BusTypeBase(BaseModel):
    name: str
    total_seats: int

class BusType(BusTypeBase):
    id: Optional[int]
    admin_id: int
    companyName: str
    created_at: Union[datetime, None] = datetime.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class BusTypeRequest(BaseModel):
    name: str
    total_seats: int

    class Config:
        from_attributes = True
        populate_by_name = True

class BusTypesResponse(BaseResponse):
    data: Union[List[BusType],None] = None

class AddBusTypeRequest(BusTypeBase):
    id: Optional[int]=None
    admin_id: int
    seats: List[SeatCreate]

class BusTypeResponse(BaseResponse):
    data: BusType = None