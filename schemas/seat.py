from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class SeatBase(BaseModel):
    seatNumber: Union[str, None] = None
    classType: Union[str, None] = None
    availabilityStatus: Union[str, None] = None


class SeatRequest(SeatBase):
    user: Union[List[str], None] = None

class Seat(SeatBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class SeatsResponse(BaseResponse):
    data: Union[List[Seat],None] = None
    
class SeatResponse(BaseResponse):
    data: Seat = None