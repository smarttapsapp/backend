from typing import Optional, Union,List,Dict
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
from schemas.request import PINRequest
from utils import util


class PaymentBase(BaseModel):
    amount: Union[str, None] = None
    payment_type: Union[str, None] = None
    reference: Union[str, None] = None
    event: Union[str, None] = None


class PaymentRequest(PaymentBase):
    user: Union[List[str], None] = None

class Payment(PaymentBase):
    id: Optional[int]
    statusMessage: Union[str, None] = None
    statusCode: Union[str, None] = None
    balanceBefore: Union[str, None] = None
    balanceAfter: Union[str, None] = None
    fee: Union[str, None] = None
    channel: Union[str, None] = None
    access_code: Union[str, None] = None
    status: Union[str, None] = None
    payment_date: Union[str, None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class GenerateQRRequest(PINRequest):
    walletNumber: str
    amount: str
    description: str
    pin: str
class PaymentsResponse(BaseResponse):
    data: Union[List[Payment],None] = None
    
class PaymentResponse(BaseResponse):
    data: Payment = None

class FundRequest(BaseModel):
    amount:str

class BuyTicketRequest(PINRequest):
    busId:int
    scheduleId: int
    walletAccount:str
    amount: str
class BuyTrainTicketRequest(PINRequest):
    trainId:int
    scheduleId: int
    walletAccount:str
    amount: int
    adult:int
    minor:int
    tripDate:datetime
class DebitRequest(PINRequest):
    walletAccount:str
    senderAccount:str
    senderPhone: str
    senderToken:str
    amount: str
    description:str
    transactionId:str
    transactionChannel:str
    transactionDate:str
class BillNameEnquiryRequest(BaseModel):
    billerId:str
    packageId:str
    customerNumber:str
    amount: str
    walletAccount:str
class BillNameEnquiryResponse(BaseResponse):
    data: Dict = None
class BillPaymentRequest(PINRequest):
    billerId:str
    packageId:Optional[str]
    customerNumber:str
    walletAccount:str
    amount: str
    @validator("amount")
    def amount_validator(cls, amount):
        formattedAmount = util.amountToKobo(amount=amount)
        return formattedAmount
    customerAddress:Optional[str]
    customerName:Optional[str]
class BillPaymentResponse(BaseResponse):
    data: Dict = None
class WalletDebitRequest(PINRequest):
    senderAccount:str
    receiverAccount:str
    receiverAccountName: str
    description:str
    amount: float