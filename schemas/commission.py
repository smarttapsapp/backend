from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse


class CommissionBase(BaseModel):
    commission_rate: Union[str, None] = None
    commission_type: Union[str, None] = None

class Commission(CommissionBase):
    id: Optional[int]
    product_type_id: Optional[int]=None
    admin_id: Optional[int]=None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AddCommissionRequest(Commission):
    busschedules:List[int]
    busroutes:List[int]
class CommissionsResponse(BaseResponse):
    data: Union[List[Commission],None] = None
    
class CommissionResponse(BaseResponse):
    data: Commission = None