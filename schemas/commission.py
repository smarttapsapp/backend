from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
from schemas.admin import AdminMini
from schemas.product_type import ProductTypeMini


class CommissionBase(BaseModel):
    commission_rate: Union[int, None] = None
    commission_type: Union[str, None] = None

class Commission(CommissionBase):
    id: Optional[int]=None
    product_type_id: int
    product_type: Optional[ProductTypeMini]=None
    admin_id: int
    admin: Optional[AdminMini]=None
    glcode: str
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class CommissionsResponse(BaseResponse):
    data: Union[List[Commission],None] = None
    
class CommissionResponse(BaseResponse):
    data: Commission = None
class AddCommissionRequest(Commission):
    pass