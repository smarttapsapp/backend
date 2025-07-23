from pydantic import BaseModel
from typing import Dict,List


class BaseResponse(BaseModel):
    statusCode: str
    statusDescription: str
    data: Dict|List | str = None