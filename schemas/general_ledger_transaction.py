from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.journal import JournalEntry


class GTransactionBase(BaseModel):
    reference:str
    transaction_type:str
    description:Union[str,None] = None
    total_amount:str
    fee_amount:str
    provider_cost :str
    commission :str
    merchant_com :str
    status:str
    posted_at : datetime
class GTransaction(GTransactionBase):
    id: Optional[int] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class GTransactionsResponse(BaseResponse):
    data: Union[List[GTransaction],None] = None
class GTransactionResponse(BaseResponse):
    data: GTransaction = None
