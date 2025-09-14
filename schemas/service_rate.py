from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.admin import AdminMini
from schemas.product_type import ProductTypeMini


class ProviderRateBase(BaseModel):
    provider_discount_rate: Union[int,float, None] = None
    provider_discount_type: Union[str, None] = None
    active: Union[bool, None] = False
class ProviderRate(ProviderRateBase):
    id: Optional[int]=None
    admin_id: int
    admin: Optional[AdminMini]=None
    product_type_id: int
    gl_to_provider: str
    product_type: Optional[ProductTypeMini]=None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class ProvidersResponse(BaseResponse):
    data: Union[List[ProviderRate],None] = None
class ProviderResponse(BaseResponse):
    data: ProviderRate = None
class AddProviderRateRequest(ProviderRate):
    pass