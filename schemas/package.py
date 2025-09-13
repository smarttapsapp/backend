from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class PackageBase(BaseModel):
    product_type_id:int
    billerId: Union[str, None] = None
    description: Union[str, None] = None
    amount: Union[str, None] = None
    validity: Union[str, None] = None
    packageCode: Union[str, None] = None
    hasValidity: Union[bool, None] = None
    status: Union[bool, None] = None
    currencyCode: Union[str, None] = None
    currencySymbol: Union[str, None] = None

class Package(PackageBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddPackageRequest(PackageBase):
    validity: Union[int, None] = None
    id: Optional[int]=None

class PackagesResponse(BaseResponse):
    data: Union[List[Package],None] = None
    
class PackageResponse(BaseResponse):
    data: Package = None