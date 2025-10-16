from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class RoleBase(BaseModel):
    name: Union[str, None] = None
    tag:str


class RoleRequest(RoleBase):
    status: Union[bool, None] = False
    user: Union[List[str], None] = None

class Role(RoleBase):
    status: Union[bool, None] = False
    identifier: Optional[str]=None
    id: Optional[int]=None

    class Config:
        from_attributes = True
        populate_by_name = True

class RolesResponse(BaseResponse):
    data: Union[List[Role],None] = None
    
class RoleResponse(BaseResponse):
    data: Role = None

class AddRoleRequest(Role):
    description: Union[str, None] = None
