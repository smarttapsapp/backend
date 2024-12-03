from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class MovableBase(BaseModel):
    name: Union[str, None] = None
    seatCount: Union[int, None] = None
    types: Union[str, None] = None


class MovableRequest(MovableBase):
    user: Union[List[str], None] = None

class Movable(MovableBase):
    tv: Union[bool, None] = False
    camera: Union[bool, None] = False
    ac: Union[bool, None] = False
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class MovablesResponse(BaseResponse):
    data: Union[List[Movable],None] = None
    
class MovableResponse(BaseResponse):
    data: Movable = None