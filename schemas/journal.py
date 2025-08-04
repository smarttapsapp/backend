from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
#from schemas.general_ledger import GLedgerMini


class JournalEntryBase(BaseModel):
    account_id: Optional[int]
    admin_id: Optional[int]
    amount: Union[str, None] = None
    is_debit: Union[bool, None] = False
class JournalEntry(JournalEntryBase):
    id: Optional[int]
    #gl_account: Optional[GLedgerMini]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class JournalEntriesResponse(BaseResponse):
    data: Union[List[JournalEntry],None] = None
class JournalEntryResponse(BaseResponse):
    data: JournalEntry = None
