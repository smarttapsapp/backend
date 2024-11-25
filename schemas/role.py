from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class RoleBase(BaseModel):
    name: Union[str, None] = None
    status: Union[bool, None] = False


class RoleRequest(RoleBase):
    user: Union[List[str], None] = None

class Role(RoleBase):
    id: Optional[int]

    class Config:
        from_attributes = True
        populate_by_name = True

class RolesResponse(BaseResponse):
    data: Union[List[Role],None] = None
    
class RoleResponse(BaseResponse):
    data: Role = None