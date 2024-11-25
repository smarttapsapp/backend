from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class DeviceBase(BaseModel):
    title: Union[str, None] = None
    type: Union[str, None] = None
    message: Union[str, None] = None


class DeviceRequest(DeviceBase):
    user: Union[List[str], None] = None

class Device(DeviceBase):
    isRead: Union[bool, None] = False
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class DevicesResponse(BaseResponse):
    data: Union[List[Device],None] = None
    
class DeviceResponse(BaseResponse):
    data: Device = None