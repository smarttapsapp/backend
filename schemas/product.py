from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.product_type import ProductType


class ProductBase(BaseModel):
    name: Union[str, None] = None
    description: Union[str, None] = None
    vasType: Union[str, None] = None
    icon: Union[str, None] = None
    customerField: Union[str, None] = None

class ProductRequest(ProductBase):
    user: Union[List[str], None] = None

class Product(ProductBase):
    enabledInline: Union[bool, None] = False
    status: Union[bool, None] = False
    id: Optional[int]
    billers: Union[List[ProductType],None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class ProductsResponse(BaseResponse):
    data: Union[List[Product],None] = None
    
class ProductResponse(BaseResponse):
    data: Product = None