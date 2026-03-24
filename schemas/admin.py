from pydantic import BaseModel, Field,validator,EmailStr
from typing import Optional, Union, List,Annotated
from schemas.otp import OTP
from utils import util
from schemas.account import Account
from datetime import datetime
from schemas.response import BaseResponse
from schemas.role import Role


class AdminMini(BaseModel):
    id: Union[int,None]=0
    companyName: Union[str,None]=None
    firstname: Union[str,None]=None
    lastname: Union[str,None]=None
    class Config:
        from_attributes = True
        populate_by_name = True
class AdminBase(BaseModel):
    firstname: str
    lastname: str
    phonenumber: str
    email: str
    companyName: Union[str,None]=None
class AdminCreate(AdminBase):
    password: Union[str, None] = None
    created_at: datetime
    updated_at: datetime
class Admin(AdminBase):
    status: bool
    role: Role
    cashout_enabled: Optional[bool]=False
    identifier: Optional[str]=None
    cashout_account: Union[str,None]=None
    cashout_limit: Union[str,None]="0"
    cashout_bank: Union[str,None]=None
    billerId: Optional[str]=None
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True
class Provider(AdminBase):
    companyName: Union[str,None]=None
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True
class AdminProfile(AdminBase):
    status: bool
    id: int
    tag: str
    cashout_enabled: Optional[bool]=False
    cashout_account: Union[str,None]=None
    cashout_bank: Union[str,None]=None
    cashout_limit: Union[str,None] = "0"
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
            cashout_enabled=obj.cashout_enabled,
            cashout_account=obj.cashout_account,
            cashout_bank=obj.cashout_bank,
            cashout_limit=obj.cashout_limit,
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
class AddCashoutAccountRequest(BaseModel):
    bankCode:str=Field(pattern="^[0-9]+$", max_length=5, min_length=3)
    accountNumber:str=Field(pattern="^[0-9]+$", max_length=10, min_length=10)
    password:str
    accountName:Optional[str]=None
class CashoutLimitRequest(BaseModel):
    amount:Annotated[int, Field(gt=50)]
    password:str
class CashoutWithdrawalRequest(BaseModel):
    amount:Annotated[int, Field(gt=50)]
    password:str
    desc:Optional[str] = None
class CashoutConfirmationRequest(BaseModel):
    amount:Annotated[int, Field(gt=50)]
    password:str
    desc:Optional[str] = None
    otp:str=Field(pattern="^[0-9]+$", max_length=6, min_length=6)
    requestType:str
    @validator("requestType")
    def requestType_validator(cls, value):
        if value not in ["WITHDRAWAL","ADD_ACCOUNT","LIMIT_CHANGE"]:
            raise ValueError("Invalid request type")
        return value
#class AdminRoutesResponse(BaseResponse):
#    data: Union[List[AdminTransport],None] = []