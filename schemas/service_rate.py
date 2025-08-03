from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class ProviderRateBase(BaseModel):
    provider_discount_rate: Union[str, None] = None
    provider_discount_type: Union[str, None] = None
    active: Union[bool, None] = False
class ProviderRate(ProviderRateBase):
    id: Optional[int]
    admin_id: Optional[int]
    product_type_id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class ProvidersResponse(BaseResponse):
    data: Union[List[ProviderRate],None] = None
class ProviderResponse(BaseResponse):
    data: ProviderRate = None
