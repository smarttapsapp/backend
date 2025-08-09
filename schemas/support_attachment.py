from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class SupportAttachmentBase(BaseModel):
    file_path: Union[str, None] = None

class SupportAttachment(SupportAttachmentBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class SupportAttachmentsResponse(BaseResponse):
    data: Union[List[SupportAttachment],None] = None
    
class SupportAttachmentResponse(BaseResponse):
    data: SupportAttachment = None