from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.request import TransactionPINRequest


class PaymentBase(BaseModel):
    title: Union[str, None] = None
    type: Union[str, None] = None
    message: Union[str, None] = None


class PaymentRequest(PaymentBase):
    user: Union[List[str], None] = None

class Payment(PaymentBase):
    isRead: Union[bool, None] = False
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class GenerateQRRequest(TransactionPINRequest):
    walletNumber: str
    amount: str
    description: str
    pin: str
class PaymentsResponse(BaseResponse):
    data: Union[List[Payment],None] = None
    
class PaymentResponse(BaseResponse):
    data: Payment = None