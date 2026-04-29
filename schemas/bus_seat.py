from typing import Optional, Union,List
from pydantic import BaseModel
from schemas.response import BaseResponse


class SeatBase(BaseModel):
    seatrow:int
    seatcolumn:int
    is_bookable:bool
    admin_id: int
    seattype: Union[str, None] = None
    seat_label: Union[str, None] = None
    
class SeatCreate(SeatBase):
    pass
class Seat(SeatBase):
    id: Optional[int]
    admin_id: int

    class Config:
        from_attributes = True
        populate_by_name = True

class SeatsResponse(BaseResponse):
    data: Union[List[Seat],None] = None

class AddSeatRequest(SeatBase):
    id: Optional[int]=None
    admin_id: int

class SeatResponse(BaseResponse):
    data: Seat = None