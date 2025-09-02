from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from models.model import *


class CashoutBase(BaseModel):
    walletCashout: Union[str, None] = None
    availableBalance: Union[str, None] = None
    message: Union[str, None] = None
    source: Union[str, None] = None
    amount: Union[str, None] = None
    recipient: Union[str, None] = None
    withdrawalStatus: Union[str, None] = None
    statusCode: Union[TransactionCodeEnum, None] = None  
    statusDescription: Union[TransactionStatusEnum, None] = None
    reference: Union[str, None] = None
    reason: Union[str, None] = None

class Cashout(CashoutBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class CashoutsResponse(BaseResponse):
    data: Union[List[Cashout],None] = None
    
class CashoutResponse(BaseResponse):
    data: Cashout = None