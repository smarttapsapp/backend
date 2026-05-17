from typing import Optional, Union,List,Dict
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,validator,Field
from schemas.response import BaseResponse
from schemas.request import PINRequest
from schemas.product import Product,ProductOut
from schemas.product_type import ProductType
from utils import util

class PaymentBase(BaseModel):
    recipient:str
    amount: str
    payment_type:str
    reference: str
    event: str
class Payment(PaymentBase):
    id: Optional[int]
    statusMessage: Union[str, None] = None
    statusCode: Union[str, None] = None
    channel: Union[str, None] = None
    status: Union[str, None] = None
    product: str
    service: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            recipient=obj.recipient,
            amount=obj.amount,
            payment_type=obj.payment_type,
            reference=obj.reference,
            event=obj.event,
            statusMessage=obj.statusMessage,
            statusCode=obj.statusCode,
            channel=obj.channel,
            status=obj.status,
            product=obj.product.name if obj.product else 'Payment',
            service=obj.productType.billerName if obj.productType else 'General',
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
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

class Payment(PaymentBase):
    id: Optional[int]
    statusMessage: Union[str, None] = None
    statusCode: Union[str, None] = None
    channel: Union[str, None] = None
    status: Union[str, None] = None
    firstname: Union[str, None] = None
    lastname: Union[str, None] = None
    productName: Union[str, None] = None
    billerName: Union[str, None] = None
    companyName: Union[str, None] = None
    providerAmount: Union[str, None] = None
    commissionAmount: Union[str, None] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    class Config:
        from_attributes = True
        populate_by_name = True
class RevenuesResponse(BaseResponse):
    data: Union[List[Payment],None] = None 
class PaymentResponse(BaseResponse):
    data: Transaction = None
class FundRequest(BaseModel):
    amount:str
    merchant:str
class AutoFundRequest(BaseModel):
    amount:str
    thresholdAmount:str
class BuyTicketRequest(PINRequest):
    walletAccount:str
    tripId: int
    amount: str
    seats:List[int]
    @validator("amount")
    def amount_validator(cls, amount):
        #formattedAmount = util.amountToKobo(amount=amount)
        return str(int(amount)*100)
class BuyTrainTicketRequest(PINRequest):
    trainId:int
    scheduleId: int
    walletAccount:str
    amount: int
    trip:int
    adult:int
    minor:int
    tripDate:datetime
    routeId:int
    seatId:int
class RedeemRequest(BaseModel):
    ticketId:str
    busNumber:str
    mode:str
    walletAccount:str
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
    billerId: Union[str, None] = "nfc"
    billerType:Union[str, None] = "payment"
class BillNameEnquiryRequest(BaseModel):
    billerId:str
    billerType:str
    packageId:str
    customerNumber:str
    amount: str
    walletAccount:str
class BillNameEnquiryResponse(BaseResponse):
    data: Dict = None
class BillPaymentRequest(PINRequest):
    billerId:str
    billerType:str
    packageId:Optional[str]
    customerNumber:str
    walletAccount:str
    amount: str
    @validator("amount")
    def amount_validator(cls, amount):
        #formattedAmount = util.amountToKobo(amount=amount)
        return str(int(amount))
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
    billerId: Union[str, None] = "wallet"
    billerType:Union[str, None] = "payment"
class VerifyCashoutRequest(BaseModel):
    bankCode:str
    accountNumber:str
class AddCashoutRequest(PINRequest):
    bankCode:str
    accountNumber:str
class CashoutRequest(PINRequest):
    amount:str
    billerId: Union[str, None] = "cashout"
    billerType:Union[str, None] = "payment"
    desc:Optional[str] = None