from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,EmailStr,validator,Field,field_validator,model_validator
from schemas.response import BaseResponse
from schemas.request import PINRequest
from schemas.account import Account
from schemas.device import Device
from utils import util


class CustomerMini(BaseModel):
    firstname: str
    lastname: str
    class Config:
        from_attributes = True
        populate_by_name = True
class CustomerBase(BaseModel):
    firstname: str
    lastname: str
    phonenumber: str
    identifier: Optional[str]=None
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
    cashout_enabled: Union[bool, None] = False
class Customer(CustomerBase):
    point_ratings: Union[str, None] = "0"
    account_ratings: Union[str, None] = "0"
    account_type: Union[str, None] = "0"
    account_status: Union[str, None] = "0"
    date_of_birth: Union[str, None] = "0"
    autoFund: Union[bool, None] = False
    profile_picture: Union[str, None] = None
    wallet:Union[Account,None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class CustomerDetails(CustomerBase):
    nin: Union[str, None] = None
    bvn: Union[str, None] = None
    state_of_origin: Union[str, None] = None
    lga_of_residence: Union[str, None] = None
    residence_address: Union[str, None] = None
    lga: Union[str, None] = None
    profile_picture: Union[str, None] = None
    next_of_kin_name: Union[str, None] = None
    next_of_kin_address: Union[str, None] = None
    next_of_kin_phone: Union[str, None] = None
    next_of_kin_relationship: Union[str, None] = None
    autoFundAmount: Union[float, None] = 0
    autoFundThreshold: Union[float, None] = 0
    point_ratings: Union[str, None] = "0"
    account_ratings: Union[str, None] = "0"
    account_type: Union[str, None] = "0"
    account_status: Union[str, None] = "0"
    date_of_birth: Union[str, None] = "0"
    autoFund: Union[bool, None] = False
    profile_picture: Union[str, None] = None
    wallet:Union[Account,None] = None
    device: Union[Device, None] = None
    preferences: Union[dict, None] = None
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class CustomerRequest(CustomerBase):
    @field_validator("password")
    def validate_password(cls, v):
        if not util.PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must contain at least: 1 uppercase, 1 lowercase, "
                "1 number, 1 special character, and be at least 8 characters long"
            )
        return util.validate_strong_password(v)
class LoginRequest(BaseModel):
    username: str
    password: str  
class OTPRequest(BaseModel):
    otp: str= Field(pattern="^[0-9]+$", max_length=6, min_length=6)
class CreatePINRequest(BaseModel):
    pin: str = Field(pattern="^[0-9]+$", max_length=4, min_length=4)
    confirmPin: str = Field( pattern="^[0-9]+$", max_length=4, min_length=4)
    @model_validator(mode="after")
    def check_pin_match(self):
        if self.pin != self.confirmPin:
            raise ValueError("PIN mismatch")
        return self
class ForgetPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    otp: str 
    password: str 
    confirmPassword: str 
    @field_validator("password")
    def validate_password(cls, v):
        if not util.PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must contain at least: 1 uppercase, 1 lowercase, "
                "1 number, 1 special character, and be at least 8 characters long"
            )
        
        return util.validate_strong_password(v)
    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Password and Confirm Password must match")
        return self
class ChangePINRequest(PINRequest):
    newPin: str= Field(pattern="^[0-9]+$", max_length=4, min_length=4)
    confirmPin: str= Field(pattern="^[0-9]+$", max_length=4, min_length=4)
    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.newPin != self.confirmPin:
            raise ValueError("PIN and Confirm PIN must match")
        return self
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
    @field_validator("password")
    def validate_password(cls, v):
        if not util.PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must contain at least: 1 uppercase, 1 lowercase, "
                "1 number, 1 special character, and be at least 8 characters long"
            )
        return util.validate_strong_password(v)
    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Password and Confirm Password must match")
        return self
class NextOfKinRequest(BaseModel):
    fullName: str
    address: str
    phone: str
    relationship: str
class UnlockRequest(BaseModel):
    pin:str
    action:str
    username: str
class CustomersResponse(BaseResponse):
    data: Union[List[Customer],None] = None
class CustomerResponse(BaseResponse):
    data: CustomerDetails = None