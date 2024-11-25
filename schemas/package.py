from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class PackageBase(BaseModel):
    title: Union[str, None] = None
    type: Union[str, None] = None
    message: Union[str, None] = None


class PackageRequest(PackageBase):
    user: Union[List[str], None] = None

class Package(PackageBase):
    isRead: Union[bool, None] = False
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class PackagesResponse(BaseResponse):
    data: Union[List[Package],None] = None
    
class PackageResponse(BaseResponse):
    data: Package = None