from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.package import Package
from schemas.admin import AdminMini

class ProductTypeMini(BaseModel):
    product_id:int
    billerName:str
    billerType: Union[str, None] = None
    logo: Union[str, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True

class ProductTypeBase(BaseModel):
    product_id:int
    billerName:str
    billerId:str
    provider:Union[AdminMini,None]=None
    provider_id:Union[int,None]=None
    billerType: Union[str, None] = None
    logo: Union[str, None] = None
    customerField: Union[str, None] = None
    hasPackages: Union[bool, None] = False
    hasLookup: Union[bool, None] = False
    hasAddons: Union[bool, None] = False
    status: Union[bool, None] = False
    maxAmountLimit: Union[int, None] = None
    minAmountLimit: Union[int, None] = None
class ProductType(ProductTypeBase):
    network: Union[str, None] = None
    id: Optional[int]
    packages: Union[List[Package],None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddProductTypeRequest(ProductTypeBase):
    id: Optional[int]=None
    
class ProductTypesResponse(BaseResponse):
    data: Union[List[ProductType],None] = None
    
class ProductTypeResponse(BaseResponse):
    data: ProductType = None
class SwitchProviderRequest(BaseModel):
    id: int
    provider_id: int
    billerName:Optional[str]