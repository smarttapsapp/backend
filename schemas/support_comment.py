from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class SupportCommentBase(BaseModel):
    comment: Union[str, None] = None

class SupportComment(SupportCommentBase):
    id: Optional[int] = None
    attachment: Optional[str] = None
    ticket_id: Optional[int]
    user_id: Optional[int] = None
    admin_id: Optional[int] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()
    class Config:
        from_attributes = True
        populate_by_name = True
class SupportTicketCommentRequest(SupportComment):
    pass

    class Config:
        from_attributes = True
        populate_by_name = True

class SupportCommentsResponse(BaseResponse):
    data: Union[List[SupportComment],None] = None
    
class SupportCommentResponse(BaseResponse):
    data: SupportComment = None