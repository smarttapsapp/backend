from pydantic import BaseModel
from typing import Dict


class BaseResponse(BaseModel):
    statusCode: str
    statusDescription: str
    data: Dict | str = None