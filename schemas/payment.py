from typing import Optional, Union,List,Dict
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator
from schemas.response import BaseResponse
from schemas.request import PINRequest
from schemas.product import Product
from schemas.product_type import ProductType
from utils import util

class PaymentBase(BaseModel):
    recipient:str
    amount: str
    payment_type:str
    reference: str
    event: str
class PaymentRequest(PaymentBase):
    user: Union[List[str], None] = None
class Payment(PaymentBase):
    id: Optional[int]
    statusMessage: Union[str, None] = None
    statusCode: Union[str, None] = None
    channel: Union[str, None] = None
    status: Union[str, None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()
    class Config:
        from_attributes = True
        populate_by_name = True
class Transaction(PaymentBase):
    statusMessage: Union[str, None] = None
    statusCode: Union[str, None] = None
    channel: Union[str, None] = None
    status: Union[str, None] = None
    payment_date: Union[str, None] = None
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()
    productType: Union[str, None] = None
    product: Union[str, None] = None
    @classmethod
    def from_orm(cls, obj):
        return cls(
            recipient=obj.recipient,
            amount=obj.amount,
            reference=obj.reference,
            payment_type=obj.payment_type,
            event=obj.event,
            statusMessage=obj.statusMessage,
            status=obj.status,
            statusCode=obj.statusCode,
            channel=obj.channel,
            payment_date=obj.payment_date,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            productType=obj.productType.billerName,
            product=obj.product.name  
        )

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
    data: Transaction = None
class FundRequest(BaseModel):
    amount:str
class AutoFundRequest(BaseModel):
    amount:str
    thresholdAmount:str
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
class RedeemRequest(BaseModel):
    ticketId:str
    busNumber:str
    mode:str
    walletAccount:str
    status:str
    expireAt:str
    amount: str
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