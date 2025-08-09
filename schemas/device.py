from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class DeviceBase(BaseModel):
    platformVersion: Union[str, None] = None
    imeiNo: Union[str, None] = None
    modelName: Union[str, None] = None
    manufacturer: Union[str, None] = None
    isPhysicalDevice: Union[bool, None] = False
    deviceName: Union[str, None] = None
    apiLevel: Union[str, None] = None


class DeviceRequest(DeviceBase):
    pass

class Device(DeviceBase):
    id: Optional[int]=None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class DevicesResponse(BaseResponse):
    data: Union[List[Device],None] = None
    
class DeviceResponse(BaseResponse):
    data: Optional[Device] = None