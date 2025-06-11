from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,EmailStr,validator,Field
from schemas.response import BaseResponse
from schemas.request import PINRequest
from schemas.account import Account
from utils import util


class CustomerBase(BaseModel):
    firstname: str
    lastname: str
    phonenumber: str
    @validator("phonenumber")
    def phoneNumber_validator(cls, phonenumber):
        phone = util.formatPhoneWithDialingCode(msisdn=phonenumber)
        return phone
    password: str
    email: str
    username: str
    nin_submitted: bool = False
    nin_verified: bool = False
    bvn_verified: bool = False
    email_verified: bool = False
    address_submitted: bool = False
    is_next_of_kin: bool = False
class Customer(CustomerBase):
    point_ratings: Union[str, None] = "0"
    account_ratings: Union[str, None] = "0"
    account_type: Union[str, None] = "0"
    account_status: Union[str, None] = "0"
    date_of_birth: Union[str, None] = "0"
    autoFund: Union[bool, None] = False
    wallet:Union[Account,None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class CustomerRequest(CustomerBase):
    pass
class LoginRequest(BaseModel):
    username: str
    password: str  
class OTPRequest(BaseModel):
    otp: str
class CreatePINRequest(BaseModel):
    pin: str = Field(examples=["0000"], pattern="^[0-9]+$", max_length=4, min_length=4)
    confirmPin: str = Field(
        examples=["0000"], pattern="^[0-9]+$", max_length=4, min_length=4
    )
class ForgetPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    otp: str 
    password: str 
    confirmPassword: str 
class ChangePINRequest(PINRequest):
    newPin: str
    confirmPin: str
class VerificationRequest(BaseModel):
    action:str
    nin: Optional[str]=None
    bvn: Optional[str]=None
    email: Optional[str]=None
    phone: Optional[str]=None
class InfoVerificationRequest(BaseModel):
    action: str
    otp: str
class ChangePasswordRequest(BaseModel):
    oldPassword: str
    password: str
    confirmPassword: str
class NextOfKinRequest(BaseModel):
    fullName: str
    address: str
    phone: str
    relationship: str
class CustomersResponse(BaseResponse):
    data: Union[List[Customer],None] = None
class CustomerResponse(BaseResponse):
    data: Customer = None