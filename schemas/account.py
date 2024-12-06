from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class AccountBase(BaseModel):
    walletAccount: Union[str, None] = None
    availableBalance: Union[str, None] = None
    message: Union[str, None] = None


class AccountRequest(AccountBase):
    user: Union[List[str], None] = None

class Account(AccountBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class AccountsResponse(BaseResponse):
    data: Union[List[Account],None] = None
    
class AccountResponse(BaseResponse):
    data: Account = None