from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.moveable import Movable

class ParkBase(BaseModel):
    name: Union[str, None] = None
    parkImage: Union[str, None] = None
    address: Union[str, None] = None
    contact: Union[str, None] = None
    startingPoint: Union[str, None] = None
    estimatedDeparture: Union[datetime, None] = None
    estimatedArrival: Union[datetime, None] = None
    destination: Union[str, None] = None
    description: Union[str, None] = None
    policy: Union[str, None] = None

class ParkRequest(ParkBase):
    user: Union[List[str], None] = None

class Park(ParkBase):
    price: Union[str, None] = None
    status: Union[bool, None] = False
    movable:Union[Movable, None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class ParksResponse(BaseResponse):
    data: Union[List[Park],None] = None
    
class ParkResponse(BaseResponse):
    data: Park = None