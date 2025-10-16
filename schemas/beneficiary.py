from pydantic import BaseModel, Field
from typing import Optional, Union, List
from datetime import datetime
from schemas.response import BaseResponse
from schemas.request import PINRequest


class BeneficiaryBase(BaseModel):
    nickname: str
    customerId: str
    transaction_type: str
    logo: Union[str, None] = None
    billercode: str
    billername: Union[str, None] = None


class BeneficiaryCreate(BeneficiaryBase):
    user_id: int
    updated_at: Union[datetime, None] = datetime.now()
    created_at: Union[datetime, None] = datetime.now()


class Beneficiary(BeneficiaryBase):
    id: int
    identifier: Optional[str] = None
    user_id: int

    class Config:
        from_attributes = True
        populate_by_name = True
class AddBeneficiaryRequest(PINRequest):
    nickname:str
    customerId:str
    transaction_type:str
    billercode: str
class BeneficiariesResponse(BaseResponse):
    data: Union[List[Beneficiary],None] = None