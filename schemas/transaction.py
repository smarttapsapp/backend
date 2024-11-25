from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class TransactionBase(BaseModel):
    transactionType: Union[str, None] = None
    transactionId: Union[str, None] = None
    amount: Union[str, None] = None
    channel: Union[str, None] = None
    transactionStatus: Union[str, None] = None
    remarks: Union[str, None] = None
    remarks: Union[str, None] = None
    remarks: Union[str, None] = None
    remarks: Union[str, None] = None


class Transaction(TransactionBase):
    isDebit: Union[bool, None] = False
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class Transactions(BaseResponse):
    data: Union[List[Transaction],None] = None
    
class TransactionResponse(BaseResponse):
    data: Transaction = None