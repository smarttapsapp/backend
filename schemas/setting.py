
from pydantic import BaseModel
from schemas.response import BaseResponse
from typing import Optional, Union,List,Sequence
from pydantic_settings import BaseSettings,SettingsConfigDict


class SettingBase(BaseModel):
    access_token_expire_minutes: int
    secret_key:  Union[str, None] = None
    algorithm:  Union[str, None] = None
    mail_username: Union[str, None] = None
    mail_password: Union[str, None] = None
    mail_from: Union[str, None] = None
    mail_port: Union[str, None] = None
    mail_server:  Union[str, None] = None
    mail_from_name:  Union[str, None] = None
    paystack_url:  Union[str, None] = None
    paystack_token:  Union[str, None] = None


class SettingRequest(SettingBase):
    pass

class Setting(SettingBase):
    id: Optional[int]

    class Config:
        from_attributes = True
        populate_by_name = True

class SettingsResponse(BaseResponse):
    data: Union[List[Setting],None] = None
    
class SettingResponse(BaseResponse):
    data: Setting = None

class AppSetting(BaseSettings):
    app_name: str
    channel_name: str
    debug: bool
    db_url: str
    allowed_hosts: Sequence[str]
    allowed_origins: Sequence[str]
    access_token_expire_minutes: int
    secret_key: str
    algorithm: str

    model_config = SettingsConfigDict(env_file=".env")