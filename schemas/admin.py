from pydantic import BaseModel, Field,validator,EmailStr
from typing import Optional, Union, List
from schemas.otp import OTP
from schemas.account import Account
from datetime import datetime
from schemas.response import BaseResponse
from schemas.role import Role


class AdminMini(BaseModel):
    firstname: str
    lastname: str
    class Config:
        from_attributes = True
        populate_by_name = True
class AdminBase(BaseModel):
    firstname: str
    lastname: str
    phonenumber: str
    email: str
class AdminCreate(AdminBase):
    password: Union[str, None] = None
    created_at: datetime
    updated_at: datetime
class Admin(AdminBase):
    status: bool
    role: Role
    identifier: Optional[str]=None
    billerId: Optional[str]=None
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True
class Provider(AdminBase):
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True
class AdminProfile(AdminBase):
    status: bool
    id: int
    tag: str
    identifier: Optional[str]=None
    wallet: Optional[Account]=None 
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            firstname=obj.firstname,
            lastname=obj.lastname,
            phonenumber=obj.phonenumber,
            status=obj.status,
            email=obj.email,
            identifier=obj.identifier,
            wallet=obj.wallet,
            tag=obj.role.tag,
        )
    class Config:
        from_attributes = True
        populate_by_name = True

class CreateAdminRequest(AdminBase):
    id:Optional[int]=None
    tag:int
    pass      
class AdminLoginRequest(BaseModel):
    username: EmailStr
    password: str  

class ForgetPasswordRequest(BaseModel):
    email: EmailStr
class ChangePasswordRequest(BaseModel):
    oldPassword: str
    password: str
    confirmPassword: str
class AdminsResponse(BaseResponse):
    data: Union[List[Admin],None] = None
class AdminResponse(BaseResponse):
    data: Admin = None
class ProvidersResponse(BaseResponse):
    data: Union[List[Provider],None] = None
#class AdminRoutesResponse(BaseResponse):
#    data: Union[List[AdminTransport],None] = []