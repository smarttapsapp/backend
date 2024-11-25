from pydantic import BaseModel, Field,validator,EmailStr
from typing import Optional, Union, List
from schemas.otp import OTP
from schemas.device import Device
from datetime import datetime
from schemas.response import BaseResponse
from schemas.role import Role


class AdminBase(BaseModel):
    firstname: str
    lastname: str
    phonenumber: str
    email: str
    status: bool
    role: Role


class AdminCreate(AdminBase):
    password: Union[str, None] = None
    created_at: datetime
    updated_at: datetime


class Admin(AdminBase):
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True
    
class CreateAdminRequest(AdminBase):
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
