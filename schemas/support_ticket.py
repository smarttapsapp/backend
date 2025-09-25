from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from models.model import PriorityEnum,OTPStatusEnum
from schemas.response import BaseResponse
from schemas.support_attachment import SupportAttachment
from schemas.support_comment import SupportComment
from schemas.customer import CustomerMini
from schemas.admin import AdminMini
class SupportTicketBase(BaseModel):
    subject:str
    description:str
    status: Union[OTPStatusEnum, None] = OTPStatusEnum.OPEN
    priority: Union[PriorityEnum, None] = PriorityEnum.INFO
class SupportTicketRequest(SupportTicketBase):
    pass
class SupportTicket(SupportTicketBase):
    id: Optional[int]
    comments: Union[List[SupportComment], None] = []
    attachments: Union[List[SupportAttachment], None] = []
    admin: Optional[AdminMini]=None
    user: Optional[CustomerMini]=None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True
class SupportTicketsResponse(BaseResponse):
    data: Union[List[SupportTicket],None] = None
class SupportTicketResponse(BaseResponse):
    data: SupportTicket = None