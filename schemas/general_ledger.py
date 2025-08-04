from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.journal import JournalEntry


class GLedgerMini(BaseModel):
    code: Union[str, None] = None
    name: Union[str, None] = None
class GLedgerBase(GLedgerMini):
    gl_type: Union[str, None] = None
    gl_balance: Union[str, None] = "0"
class GLedger(GLedgerBase):
    id: Optional[int] = None
    journal_entries: Union[List[JournalEntry],None] = []
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class GLedgersResponse(BaseResponse):
    data: Union[List[GLedger],None] = None
class GLedgerResponse(BaseResponse):
    data: GLedger = None
class AddGLRequest(GLedgerBase):
    id: Optional[int] = None
