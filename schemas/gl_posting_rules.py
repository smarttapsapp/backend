from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse
from schemas.journal import JournalEntry


class PostingRulesBase(BaseModel):
    transaction_type :str
    entry_type :str
    account_role:str
    account_code:str
    is_active:bool
    priority :int
class PostingRules(PostingRulesBase):
    id: Optional[int] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class PostingRulessResponse(BaseResponse):
    data: Union[List[PostingRules],None] = None
class PostingRulesResponse(BaseResponse):
    data: PostingRules = None
class AddPostingRuleRequest(PostingRulesBase):
    id: Optional[int] = None
