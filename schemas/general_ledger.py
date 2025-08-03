from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class GLedgerBase(BaseModel):
    code: Union[str, None] = None
    name: Union[str, None] = None
    gl_type: Union[str, None] = None
    gl_balance: Union[str, None] = "0"
class GLedger(GLedgerBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class GLedgersResponse(BaseResponse):
    data: Union[List[GLedger],None] = None
class GLedgerResponse(BaseResponse):
    data: GLedger = None


