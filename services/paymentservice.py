
import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import select,update
from models.model import *
from models.queries import paymentQuery,queries,adminQuery
from datetime import datetime
from utils import util
from schemas.setting import Setting
from services.notificationservice import notifyUser
from services import glAccountingService,topupboxservice
from utils.constant import *
from schemas.customer import *
from schemas.payment import *
from schemas.cashout import *
from services import notificationservice
from schemas.ticket import TicketResponse,TicketsResponse
from schemas.admin import Admin
from task.tasks import process_gl_transactions,process_bills_payment,process_cashout_payment
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)
def saveFundThreshold(
        user:CustomerModel,
        request: Request,
        db: Session,
        response: Response,
        setting: Setting,payload:AutoFundRequest,
        background_task:BackgroundTasks,):
    try:
        if user.hasAuthToken:
            logger.info(f"card info is available {user.cards}")
            user.autoFund = True
            user.autoFundThreshold = payload.thresholdAmount
            user.autoFundAmount = payload.amount
            user.updated_at = datetime.now()
            saved = queries.create(db=db,model=user)
            if saved:
                message = f"You have setup auto fund of ₦{util.kobo_to_naira(int(payload.amount)):,.2f} for your purse with a threshold of ₦{util.kobo_to_naira(int(payload.thresholdAmount)):,.2f} at {datetime.now().strftime('%B %d, %Y %I:%M %p')}"
                background_task.add_task(notifyUser,db=db,title=f"Auto Fund Purse", message=message,userId=user.id, setting=setting)
                email_debit = util.templates.TemplateResponse("autofund.html",{"request": request, "user": user,"message":message},)
                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Auto Fund Purse",toAddress=user.email)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=AUTOFUNDERROR)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def toggleFundThreshold(
        user:CustomerModel,
        request: Request,
        db: Session,
        response: Response,
        setting: Setting,
        background_task:BackgroundTasks,):
    try:
        user.autoFund = not user.autoFund
        user.updated_at = datetime.now()
        saved = queries.create(db=db,model=user)
        if saved:
            message = f'You have succesfully deactivated auto fund from your purse at {datetime.now().strftime("%B %d, %Y %I:%M %p")}'
            background_task.add_task(notifyUser,db=db,title=f"Deactivate Auto Fund Purse", message=message,userId=user.id, setting=setting)
            email_debit = util.templates.TemplateResponse("autofund.html",{"request": request, "user": user,"message":message},)
            background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Deactivate Auto Fund Purse",toAddress=user.email)
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def fundPurse(
        user:Customer,
        db: Session,
        response: Response,
        setting: Setting,payload:FundRequest):
    try:
        product = queries.getBillByVas(db=db,vasType="payment")
        if product:
            creditProductType = util.find_item(product.billers,"billerId","credit")
            if creditProductType:
                payment = PaymentModel(
                    wallet_id = user.wallet.id,
                    user_id = user.id,
                    amount = payload.amount,
                    channel = ChannelEnum.OPAY if payload.merchant.lower() == "opay" else ChannelEnum.PAYSTACK,
                    product_type_id = creditProductType.id,
                    product_id=product.id,
                    event = "initialize",
                    reference=f"OPAY-{util.generateId()}",
                    statusCode = TransactionCodeEnum.PENDING,
                    statusDescription = TransactionStatusEnum.PENDING,
                    recipient=user.wallet.walletAccount,
                    payment_type = PaymentEnum.CREDIT,
                    created_at = datetime.now(),
                    updated_at= datetime.now(),
                )
                createdPayment = paymentQuery.create_payment(db=db,payment=payment)
                if createdPayment:
                    if createdPayment.channel == ChannelEnum.OPAY:
                        return await paywithopay(user=user,db=db,response=response,setting=setting,payload=payload,payment=createdPayment)
                    else:
                        return await paywithpaystack(user=user,db=db,response=response,setting=setting,payload=payload,payment=createdPayment)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def paywithopay(user:Customer,db: Session,response: Response,setting: Setting,payload:FundRequest,payment:PaymentModel):
    try:
        headers =  {'Authorization': f'Bearer {setting.opay_token}','MerchantId':setting.opay_merchantid,'content-type': 'application/json'}
        params = {
                "country": "NG",
                "reference": payment.reference,
                "amount": {
                    "total": payload.amount,
                    "currency": "NGN"
                },
                "returnUrl": f"{setting.app_url}payment/notification/opay",
                "displayName":setting.app_name,
                "customerVisitSource": "IOS",
                "evokeOpay":True,
                "expireAt":300,
                "sn":"PE462xxxxxxxx",
                "userInfo":{
                        "userEmail":user.email,
                        "userId":user.username,
                        "userMobile":util.formatPhoneShort(user.phonenumber),
                        "userName":f"{user.firstname} {user.lastname}"
                },
                "product":{
                    "description":"description",
                    "name":"name"
                },
            }
        result = util.http(f"{setting.opay_url}international/cashier/create",params=params,headers=headers)
        if result.status_code == 200:
            opayResponse = result.json()
            if opayResponse and opayResponse["code"] == "00000":
                payment.transactionreference = opayResponse["data"]["orderNo"]
                payment.access_code = opayResponse["data"]["orderNo"]
                payment.statusCode = TransactionCodeEnum.PROCESSING
                payment.statusDescription = TransactionStatusEnum.PROCESSING
                payment.statusMessage = opayResponse["message"]
                data = {"authorization_url":opayResponse["data"]["cashierUrl"],"access_code":opayResponse["data"]["orderNo"],"reference":opayResponse["data"]["reference"]}
                appResponse = BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=opayResponse["message"],data=data)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                payment.statusCode = str(status.HTTP_400_BAD_REQUEST)
                payment.statusMessage = opayResponse["message"]
                appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=opayResponse["message"])
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            payment.statusCode = str(status.HTTP_400_BAD_REQUEST)
            payment.statusMessage = "Failed"
            appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
        updatePayment = paymentQuery.create_payment(db=db,payment=payment)
        if updatePayment:
            return appResponse
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def paywithpaystack(
        user:Customer,
        db: Session,
        response: Response,
        setting: Setting,payload:FundRequest,payment:PaymentModel):
    try:
        headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
        params = {"email": user.email,"amount": payload.amount}
        result = util.http(f"{setting.paystack_url}transaction/initialize",params=params,headers=headers)
        if result.status_code == 200:
            paystackResponse = result.json()
            if paystackResponse and paystackResponse["status"] is True:
                payment.reference = paystackResponse["data"]["reference"]
                payment.access_code = paystackResponse["data"]["access_code"]
                payment.statusCode = TransactionCodeEnum.PROCESSING
                payment.statusDescription = TransactionStatusEnum.PROCESSING
                payment.statusMessage = paystackResponse["message"]
                appResponse = BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=paystackResponse["message"],data=paystackResponse["data"])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                payment.statusCode = TransactionCodeEnum.FAILED
                payment.statusMessage = paystackResponse["message"]
                appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse["message"])
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            payment.statusCode =  TransactionCodeEnum.FAILED
            payment.statusMessage = "Failed"
            appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
        payment.event = "initialize"
        updatePayment = paymentQuery.create_payment(db=db,payment=payment)
        if updatePayment:
            return appResponse
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def paystackNotification(
    request: Request,
    db: Session,
    setting: Setting,
    response: Response,
    background_task: BackgroundTasks,):
    try:
        json_data = await request.json()
        logger.info(f"incoming payment from paystack {str(json_data)}")
        payment = paymentQuery.getPaymentByReference(db=db,reference=json_data["data"]["reference"])
        if payment:
            if payment.status != "success":
                payment.event = json_data["event"]
                payment.channel = json_data["data"]["channel"]
                payment.status = json_data["data"]["status"]
                payment.fee = json_data["data"]["fees"]
                payment.paystack_id = json_data["data"]["id"]
                payment.payment_date = json_data["data"]["paid_at"]
                payment.transactionreference = json_data["data"]["id"]
                payment.statusCode = TransactionCodeEnum.SUCCESS
                payment.statusDescription = TransactionStatusEnum.SUCCESS
                payment.statusMessage = TransactionStatusEnum.SUCCESS.value
                payment.balanceBefore = payment.wallet.availableBalance
                payment.balanceAfter = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
                payment.wallet.availableBalance = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
                payment.updated_at = datetime.now()
                payment.wallet.updated_at = datetime.now()
                payment.provider_code = setting.gl_outflow
                payment.user.hasAuthToken = True
                updatedPayment = paymentQuery.create_payment(db=db,payment=payment)
                if updatedPayment:
                    card = paymentQuery.getCardByLast4(db=db,last4=json_data["data"]["authorization"]["last4"])
                    if card is None:
                        createCard = CardsModel(
                                user_id= payment.user_id,
                                authorization_code=json_data["data"]["authorization"]["authorization_code"],
                                bin=json_data["data"]["authorization"]["bin"],
                                last4=json_data["data"]["authorization"]["last4"],
                                exp_month=json_data["data"]["authorization"]["exp_month"],
                                exp_year=json_data["data"]["authorization"]["exp_year"],
                                channel=json_data["data"]["authorization"]["channel"],
                                card_type=json_data["data"]["authorization"]["card_type"],
                                bank=json_data["data"]["authorization"]["bank"],
                                signature=json_data["data"]["authorization"]["signature"],
                                account_name=json_data["data"]["authorization"]["account_name"],
                                reusable=json_data["data"]["authorization"]["reusable"],
                                created_at=datetime.now(),
                                updated_at=datetime.now(),
                            )
                        addCard = paymentQuery.create_card(db=db,card=createCard)
                    msg = f"Your purse has been funded with ₦{util.kobo_to_naira(int(updatedPayment.amount)):,.2f} successfully."
                    await glAccountingService.post_funding_gl(db=db,reference=json_data["data"]["reference"],transaction_type="payment",customer_id=payment.user_id,amount = json_data["data"]["amount"])
                    background_task.add_task(notifyUser,db=db,title=f"Fund Notification", message=msg,userId=payment.user_id, setting=setting)
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to add fund",)
            else:
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription="Payment Already confirmed",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Payment not found",)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def opayNotification(
    request: Request,
    db: Session,
    setting: Setting,
    response: Response,
    background_task: BackgroundTasks,):
    try:
        json_data = await request.json()
        logger.info(f"incoming payment from opay {str(json_data)}")
        paymentPayload = json_data.get('payload',None)
        if json_data.get('type',None) == 'transaction-status' and paymentPayload:
            payment = paymentQuery.getPaymentByReference(db=db,reference=paymentPayload["reference"])
            if str(paymentPayload["status"]).upper() == 'SUCCESS':
                if payment and payment.event != 'charge.success':
                    payment.event = 'charge.success'
                    payment.channel = ChannelEnum.OPAY
                    payment.payment_date = paymentPayload["updated_at"]
                    payment.status = paymentPayload["status"]
                    payment.fee = paymentPayload["fee"]
                    payment.paystack_id = paymentPayload["transactionId"]
                    payment.transactionreference = paymentPayload["transactionId"]
                    payment.statusCode = TransactionCodeEnum.SUCCESS
                    payment.statusDescription = TransactionStatusEnum.SUCCESS
                    payment.statusMessage = TransactionStatusEnum.SUCCESS.value
                    payment.balanceBefore = payment.wallet.availableBalance
                    payment.balanceAfter = str(int(payment.wallet.availableBalance)+int(paymentPayload["amount"]))
                    payment.wallet.availableBalance = str(int(payment.wallet.availableBalance)+int(paymentPayload["amount"]))
                    payment.updated_at = datetime.now()
                    payment.wallet.updated_at = datetime.now()
                    payment.provider_code = setting.gl_outflow
                    updatedPayment = paymentQuery.create_payment(db=db,payment=payment)
                    if updatedPayment:
                        msg = f"Your purse has been funded with ₦{util.kobo_to_naira(int(paymentPayload['amount'])):,.2f} successfully."
                        await glAccountingService.post_funding_gl(db=db,reference=paymentPayload["reference"],transaction_type="payment",customer_id=payment.user_id, amount = paymentPayload["amount"])
                        background_task.add_task(notifyUser,db=db,title=f"Fund Notification", message=msg,userId=payment.user_id, setting=setting)
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
                    else:
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=PENDING,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Payment not found or already processed",)
            else:
                payment.event = 'charge.failed'
                payment.channel = ChannelEnum.OPAY
                payment.payment_date = paymentPayload["updated_at"]
                payment.status = paymentPayload["status"]
                payment.fee = paymentPayload["fee"]
                payment.paystack_id = paymentPayload["transactionId"]
                payment.statusCode = TransactionCodeEnum.FAILED
                payment.statusDescription = TransactionStatusEnum.FAILED
                payment.statusMessage = TransactionStatusEnum.FAILED.value
                paymentQuery.create_payment(db=db,payment=payment)
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=TransactionStatusEnum.FAILED.value,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def payments(request: Request,response: Response,setting: Setting,db: Session,user: Customer,startDate: str,endDate: str,transactionType: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate} for {transactionType}"
        )
        if transactionType:
            payments = queries.getPaymentHistoriesByTransaction(db=db,userId=user.id,startDate=startDate,endDate=endDate,transType=transactionType)
        else:
            payments = queries.getPaymentHistories(db=db,userId=user.id,startDate=startDate,endDate=endDate)
        return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=[Payment.from_orm(payment).model_dump() for payment in payments]
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getSinglePayment(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Customer,
    transactionId: str ,
    transactionType: str ,
):
    try:
        logger.info(f"started transaction querying for {transactionId}")
        payment = queries.paymentByTransactionNumber(db=db,mode=PaymentEnum[transactionType.upper()],transactionId=transactionId,userId=user.id)
        if payment:
            return PaymentResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=Transaction.from_orm(payment)
            )
        response.status_code = status.HTTP_404_NOT_FOUND
        return PaymentResponse(
               statusCode=str(status.HTTP_404_NOT_FOUND),
               statusDescription=UNKNOWNTRANSACTION,
        )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(
               statusCode=str(status.HTTP_400_BAD_REQUEST),
               statusDescription=SYSTEMBUSY,
        )
async def payment(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Admin,
    transactionId: str ,
):
    try:
        logger.info(f"started transaction querying for {transactionId}")
        if transactionId:
            response.status_code = status.HTTP_200_OK
            return PaymentResponse(
              
                   statusCode=str(status.HTTP_200_OK),
                   statusDescription=SUCCESS,
                   data=paymentQuery.get_one(
                        db=db,
                        sql=QUERYSINGLETRANSACTION.replace(
                            "<userId>", str(user.id)
                        ).replace("<transactionId>", transactionId),
                    ),
             
            )
        else:
            response.status_code = status.HTTP_200_OK
            return PaymentResponse(
              
                   statusCode=str(status.HTTP_200_OK),
                   statusDescription=UNKNOWNTRANSACTION,
             
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(
          
               statusCode=str(status.HTTP_400_BAD_REQUEST),
               statusDescription=str(ex),
         
        )
async def nfcdebitService(payload:DebitRequest,request: Request,response: Response,setting: Setting,db: Session,user: Customer,background_task:BackgroundTasks):
    try:
        logger.info(f"{payload.senderAccount} started debit transaction via NFC for {payload.billerId} sender {payload.senderAccount} to receiver {payload.walletAccount}")
        sender = paymentQuery.querySender(db=db,walletAccount=payload.senderAccount)
        if sender:
            verifiedPIN = util.verify_password(payload.pin,sender.user.pin)
            if verifiedPIN:
                if payload.senderAccount != user.wallet.walletAccount:
                    duplicate = paymentQuery.getPaymentByReference(db=db,reference=payload.transactionId)
                    if duplicate:
                        logger.info(f"{payload.senderAccount} duplicate transaction found {duplicate.reference}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=DUPLICATE)
                    logger.info(f"{payload.senderAccount} started payment for biller {payload.billerId} for amount {payload.billerType} at {datetime.now()}")
                    productType = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId, billerType=payload.billerType)
                    if not productType:
                        logger.info(f"Product Type not configured at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
                    if not productType.provider:
                        logger.info(f"{payload.senderAccount} Provider not configured at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
                    serviceCharge = queries.getServiceProviderByProduct(db=db,productTypeId=productType.id)
                    if not serviceCharge:
                        logger.info(f"{payload.senderAccount} Service charge not configured at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
                    logger.info(f"{payload.senderAccount}  {serviceCharge.admin.companyName}  is configured configured at {datetime.now()}")
                    provider_cost = int(serviceCharge.provider_discount_rate) if serviceCharge.provider_discount_type == CommissionType.calculated else int(payload.amount) * (serviceCharge.provider_discount_rate/100)
                    amountToDebit = int(payload.amount) + provider_cost
                    if float(sender.availableBalance) < float(amountToDebit):
                        logger.info(f"{payload.senderAccount} Insufficient fund to send fund at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = INSUFFICIENTFUND)
                    transactionReference = f"{str(productType.billerId[:2]).upper()}-{util.generateId()}"
                    debitvalues ={"availableBalance":int(sender.availableBalance) - int(amountToDebit),"updated_at":datetime.now()}
                    creditvalues ={"availableBalance":int(user.wallet.availableBalance) + int(payload.amount),"updated_at":datetime.now()}
                    db.execute(update(AccountModel).where(AccountModel.id == sender.id).values(**debitvalues).execution_options(synchronize_session="fetch"))
                    db.execute(update(AccountModel).where(AccountModel.id == user.wallet.id).values(**creditvalues).execution_options(synchronize_session="fetch"))
                    paymentRecord = [
                        PaymentModel(
                        wallet_id = sender.id,
                        user_id = sender.user_id, 
                        amount = int(payload.amount),
                        payment_type = PaymentEnum.DEBIT,
                        reference =payload.transactionId,
                        event = "charge.success",
                        status = "success",
                        channel = payload.transactionChannel if payload.transactionChannel else  ChannelEnum.NFC,
                        providerAmount = 0,
                        statusCode = TransactionCodeEnum.SUCCESS,
                        statusDescription = TransactionStatusEnum.SUCCESS,
                        commissionAmount = 0,
                        transactionreference=transactionReference,
                        product_type_id = productType.id,product_id=productType.product_id,
                        recipient=sender.walletAccount,statusMessage = payload.description,
                        balanceBefore = sender.availableBalance,balanceAfter = sender.availableBalance,
                        created_at =datetime.now(),updated_at = datetime.now()),
                        PaymentModel(
                        wallet_id = sender.id,
                        user_id = sender.user_id, 
                        amount = int(provider_cost),
                        payment_type = PaymentEnum.DEBIT,
                        reference =f"SVC-{util.generateId()}",
                        event = "charge.success",
                        status = "success",
                        channel =payload.transactionChannel if payload.transactionChannel else  ChannelEnum.NFC,
                        providerAmount = 0,
                        statusCode = TransactionCodeEnum.SUCCESS,
                        statusDescription = TransactionStatusEnum.SUCCESS,
                        commissionAmount = 0,
                        transactionreference=payload.transactionId,
                        product_type_id = productType.id,product_id=productType.product_id,
                        recipient=sender.walletAccount,statusMessage = payload.description,
                        balanceBefore = sender.availableBalance,balanceAfter = sender.availableBalance,
                        created_at =datetime.now(),updated_at = datetime.now()),
                        PaymentModel(
                        wallet_id = user.wallet.id,
                        user_id = user.id, 
                        amount = int(payload.amount),
                        payment_type = PaymentEnum.CREDIT,
                        transactionreference = payload.transactionId,
                        event = "charge.success",
                        status = "success",
                        channel =payload.transactionChannel if payload.transactionChannel else  ChannelEnum.NFCC,
                        providerAmount = 0,
                        statusCode = TransactionCodeEnum.SUCCESS,
                        statusDescription = TransactionStatusEnum.SUCCESS,
                        commissionAmount = 0,
                        reference=f"{str(productType.billerId[:2]).upper()}-{util.generateId()}",
                        product_type_id = productType.id,product_id=productType.product_id,
                        recipient=sender.walletAccount,statusMessage = payload.description,
                        balanceBefore = user.wallet.availableBalance,balanceAfter = user.wallet.availableBalance,
                        created_at =datetime.now(),updated_at = datetime.now())
                    ]
                    db.add_all(paymentRecord)
                    db.commit()
                    process_gl_transactions.delay(payload.transactionId)
                    return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":payload.transactionId})
                    #updatedWallet = queries.updateWallet(db=db,id=user.wallet.id,values=creditvalues)
                    #updatedWallet = queries.updateWallet(db=db,id=sender.id,values=values)
                    #if not updatedWallet:
                    #    logger.info(f"{payload.senderAccount} unable to debit wallet at {datetime.now()}")
                    #    response.status_code = status.HTTP_400_BAD_REQUEST
                    #    return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = INSUFFICIENTFUND)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SAMEACCOUNT,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDPIN)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def debitNfc(payload:DebitRequest,request: Request,response: Response,setting: Setting,db: Session,user: Customer,sender:AccountModel,ecipient:AccountModel,productType:ProductTypeModel):
    try:
        if productType:
            discount = queries.getServiceProviderByProduct(db=db,productTypeId=productType.id)
            if discount:
                if productType.provider:
                    logger.info(f"{discount.admin.companyName}  is configured configured at {datetime.now()}")
                    provider_cost = int(discount.provider_discount_rate) if discount.provider_discount_type == CommissionType.calculated else amount * (1 - discount.provider_discount_rate)
                    netIncome = amount + provider_cost

            debitReference = f"{str(biller.billerId[:2]).upper()}-{payload.transactionId}"
            # debit customer
            logger.info(f"started debit for customer account {sender.walletAccount} at {datetime.now()}")
            sender.availableBalance = int(sender.availableBalance) - int(payload.amount)
            sender.updated_at = datetime.now()
            sender.payments.append(PaymentModel(
                wallet_id = sender.id,user_id =sender.user_id, amount = int(payload.amount),
                payment_type =PaymentEnum.DEBIT,reference =debitReference,
                event = "charge.success",status = "success",channel =ChannelEnum.NFC,providerAmount = 0,
                statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,
                commissionAmount = 0,transactionreference=payload.transactionId,product_type_id = biller.id,product_id=biller.product_id,
                recipient=sender.walletAccount,statusMessage = payload.description,balanceBefore = sender.availableBalance,
                balanceAfter = sender.availableBalance,created_at =datetime.now(),updated_at = datetime.now())),
            logger.info(f"balance after debit posted successfully is {sender.availableBalance}")
            savedSender = adminQuery.save(db=db,account=sender)
            if savedSender:
                creditReference = f"CR-{payload.transactionId}"
                background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
                recipient.availableBalance = int(recipient.availableBalance) + int(payload.amount)
                recipient.updated_at = datetime.now()
                recipient.payments.append(PaymentModel(
                    wallet_id = recipient.id,user_id = recipient.user_id,amount = int(payload.amount),
                    payment_type =PaymentEnum.CREDIT,reference = creditReference,
                    transactionreference=payload.transactionId,commissionAmount = 0,fee = 0,
                    event = "charge.success",status = "success",channel = ChannelEnum.NFC,
                    statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,
                    product_type_id = biller.id,product_id=biller.product_id,
                    recipient=recipient.walletAccount,statusMessage = payload.description,balanceBefore = recipient.availableBalance,
                    balanceAfter =recipient.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                creditProductType = util.find_item(product.billers,"billerId","credit")
                logger.info(f"create credit record for reciever {recipient.walletAccount} with balance after {recipient.availableBalance}")
                savedRecipient = adminQuery.create(db=db,model=recipient)
                if savedRecipient:
                    background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                    return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":debitReference})
                logger.info(f"unable to credit recipient at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
            logger.info(f"unable to debit sender at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
        logger.info(f"service not configured at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)    
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
async def debitNfcConfirmation(
    request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: CustomerModel,
    transactionId: str ,
    transactionType: str ,
):
    try:
        logger.info(f"started transaction querying for {transactionId}")
        payment = queries.queryNFCPayment(db=db,mode=PaymentEnum[transactionType.upper()],transactionId=transactionId,userId=user.id)
        if payment:
            return PaymentResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=Transaction.from_orm(payment)
            )
        response.status_code = status.HTTP_404_NOT_FOUND
        return PaymentResponse(
               statusCode=str(status.HTTP_404_NOT_FOUND),
               statusDescription=UNKNOWNTRANSACTION,
        )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(
               statusCode=str(status.HTTP_400_BAD_REQUEST),
               statusDescription=SYSTEMBUSY,
        )
async def billerEnquiry(
        payload:BillNameEnquiryRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: Customer
):
    biller = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId,billerType=payload.billerType)
    if payload.customerNumber:
        if biller:
            package = next((x for x in biller.packages if x.packageCode == payload.packageId), None)
            if package:
                if biller.billerType == "electricity":
                    topup = await topupboxservice.billEnquriesService(serviceprovider=biller.provider,customerId=payload.customerNumber,billerId=payload.packageId)
                    if topup and topup['statuscode'] == "200":
                        return BillNameEnquiryResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=topup['data'])
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=topup['message'])
                else:
                    topup = await topupboxservice.billEnquriesService(serviceprovider=biller.provider,customerId=payload.customerNumber,billerId=payload.billerId)
                    if topup and topup['statuscode'] == "200":
                        return BillNameEnquiryResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=topup['data'])
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=topup['message'])
            else:
                logger.info(f"Invalid package code selected {payload.packageId}")    
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
        logger.info(f"Invalid biller selected {payload.billerId}")    
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INCOMPLETE)
async def payBills(
        payload:BillPaymentRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks
):
    try:
        walletAccount = paymentQuery.querySender(db=db,walletAccount=payload.walletAccount)
        if not walletAccount:
            logger.info(f"{payload.walletAccount} Account not found at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        logger.info(f"started bill payment for biller {payload.billerId} for amount {payload.billerType}")
        productType = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId, billerType=payload.billerType)
        if not productType:
            logger.info(f"Product Type not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        provider = queries.getAdminById(db=db,adminId=productType.provider_id)
        if not provider:
            logger.info(f"{payload.senderAccount} Provider not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        if productType.hasPackages:
            package = next((x for x in biller.packages if x.packageCode == payload.packageId), None)
            if not package:
                logger.info(f"Invalid package code selected {payload.packageId}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Package cannot be empty")
            if package.amount and package.amount != payload.amount:
                logger.info(f"Invalid package code selected {payload.packageId}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Amount cannot be empty")
        serviceDiscount = queries.getServiceProviderByProduct(db=db,productTypeId=productType.id)
        if not serviceDiscount:
            logger.info(f"{payload.customerNumber} Service charge not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        logger.info(f"{payload.customerNumber}  {serviceDiscount.admin.companyName}  is configured configured at {datetime.now()}")
        provider_cost = (int(payload.amount) - int(serviceDiscount.provider_discount_rate)) if serviceDiscount.provider_discount_type == CommissionType.calculated else int(payload.amount) * (1- serviceDiscount.provider_discount_rate/100)
        commssionAmount = int(payload.amount) - provider_cost
        if float(walletAccount.availableBalance) < float(payload.amount):
            logger.info(f"{payload.customerNumber} Insufficient fund to send fund at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = INSUFFICIENTFUND)
        trnxId = util.generateId()
        debitvalues ={"availableBalance":int(walletAccount.availableBalance) - int(payload.amount),"updated_at":datetime.now()}
        db.execute(update(AccountModel).where(AccountModel.id == walletAccount.id).values(**debitvalues).execution_options(synchronize_session="fetch"))
        creditvalues ={"availableBalance":int(provider.wallet.availableBalance) + int(provider_cost),"updated_at":datetime.now()}
        db.execute(update(AccountModel).where(AccountModel.id == provider.wallet.id).values(**creditvalues).execution_options(synchronize_session="fetch"))
        paymentRecord = [PaymentModel(
                        wallet_id = walletAccount.id,
                        user_id = walletAccount.user_id, 
                        amount = int(payload.amount),
                        payment_type = PaymentEnum.DEBIT,
                        reference =trnxId,
                        event = "charge.success",
                        status = "success",
                        channel = ChannelEnum.MOBILE,
                        providerAmount = provider_cost,
                        statusCode = TransactionCodeEnum.PROCESSING,
                        statusDescription = TransactionStatusEnum.PROCESSING,
                        statusMessage =f"{productType.billerType} Purchase",
                        commissionAmount = commssionAmount,
                        transactionreference=trnxId,
                        product_type_id = productType.id,product_id=productType.product_id,
                        packageId= package.packageCode if productType.hasPackages and package else None,
                        provider_code = provider.billerId,
                        recipient=payload.customerNumber,
                        balanceBefore = walletAccount.availableBalance,balanceAfter = walletAccount.availableBalance,
                        created_at =datetime.now(),updated_at = datetime.now()),
                        PaymentModel(
                        wallet_id = provider.wallet.id,
                        admin_id = provider.id, 
                        amount = provider_cost,
                        payment_type = PaymentEnum.CREDIT,
                        reference =util.generateId(),
                        event = "charge.success",
                        status = "success",
                        channel = ChannelEnum.MOBILE,
                        providerAmount = provider_cost,
                        statusCode = TransactionCodeEnum.PROCESSING,
                        statusDescription = TransactionStatusEnum.PROCESSING,
                        statusMessage =f"{productType.billerType} Purchase",
                        commissionAmount = commssionAmount,
                        transactionreference=trnxId,
                        product_type_id = productType.id,product_id=productType.product_id,
                        packageId=package.packageCode if productType.hasPackages and package else None,
                        provider_code = provider.billerId,
                        recipient=payload.customerNumber,
                        balanceBefore = provider.wallet.availableBalance,balanceAfter = provider.wallet.availableBalance,
                        created_at =datetime.now(),updated_at = datetime.now())
                          ]
        db.add_all(paymentRecord)
        db.commit()
        process_bills_payment.delay(trnxId)
        return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":trnxId})
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def debitBillPayment(
        biller:ProductTypeModel,
        payload:BillPaymentRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks,
        package:PackageModel=None,
):
    logger.info(f"Started debit process for bill payment {payload.billerId} for amount {payload.amount}")
    if int(user.wallet.availableBalance) > int(payload.amount):
        logger.info(f"balance is sufficient {user.wallet.availableBalance}")
        # debit customer 
        user.wallet.availableBalance = int(user.wallet.availableBalance) - int(payload.amount)
        user.wallet.updated_at = datetime.now()
        trnxId = util.generateId()
        logger.info(f"started saving debit for customer at {datetime.now()}")
        user.wallet.payments.append(
            PaymentModel(
                wallet_id = user.wallet.id,user_id =user.id, amount = int(payload.amount),
                payment_type =PaymentEnum.DEBIT,reference =trnxId,event = "charge.success",
                provider_code= biller.provider.billerId,status = "success",channel =ChannelEnum.MOBILE,
                statusCode = TransactionCodeEnum.PROCESSING,statusDescription = TransactionStatusEnum.PROCESSING,
                product_type_id = biller.id,product_id=biller.product_id,recipient=payload.customerNumber,
                statusMessage =f"{biller.billerType} Purchase",balanceBefore = user.wallet.availableBalance,
                balanceAfter = user.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
        savedCustomerAccount = paymentQuery.create(db=db,model=user)
        if savedCustomerAccount:
            logger.info(f"saved payment for customer at {datetime.now()}")
            background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
            #background_task.add_task(notifyUser,db=db,title=f"Debit Notification", message=createDebitRecord.statusMessage,userId=user.id, setting=setting)
            #email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"payment":createDebitRecord},)
            #background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Debit Notification",toAddress=user.email)
            currentPayment = paymentQuery.getPaymentByReference(db=db,reference=trnxId)
            if currentPayment:
                logger.info(f"getting the current payment {biller.billerName} {biller.provider_id}for processing at {datetime.now()}")
                logger.info(f"getting the current payment {currentPayment.reference} for processing at {datetime.now()}")
                params = {}
                if biller.billerType == "airtime":
                    params['amount'] = str(int(payload.amount)/100)
                    params['beneficiary'] = payload.customerNumber
                    params['customer_reference'] = trnxId
                if biller.billerType == "data" and package:
                    params['amount'] = str(int(payload.amount)/100)
                    params['beneficiary'] = payload.customerNumber
                    params['customer_reference'] = trnxId
                    params['tariffTypeId'] = package.packageCode
                if biller.billerType == "cabletv" and package:
                    params['service_type'] = biller.billerId
                    params['product_code'] = package.packageCode
                    params['total_amount'] = str(int(payload.amount)/100)
                    params['smartcard_number'] = payload.customerNumber
                    params['product_monthsPaidFor'] = package.validity
                    params['addon_code'] = []
                    params['secret'] = trnxId
                    params['agentId'] = "205"
                if biller.billerType == "electricity" and package:
                    params['account_number'] = payload.customerNumber
                    params['service_type'] = package.packageCode
                    params['amount'] = str(int(payload.amount)/100)
                    params['metadata'] = package.packageCode
                    params['phone'] = package.packageCode
                    params['agentId'] = "205"
                    params['secret'] = trnxId
                topup = await topupboxservice.purchaseService(biller=biller,serviceprovider=biller.provider,params=params)
                if topup and topup['statuscode'] == "200":
                    currentPayment.statusCode = TransactionCodeEnum.SUCCESS
                    currentPayment.statusDescription = TransactionStatusEnum.SUCCESS
                    currentPayment.updated_at = datetime.now()
                    background_task.add_task(glAccountingService.debitTransaction,response=response,setting=setting,db=db,biller=biller,customerAccount=user.wallet,amount=int(payload.amount),background_task=background_task,remark=currentPayment.statusMessage)
                    return BillPaymentResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":currentPayment.reference})
                else:
                    currentPayment.statusCode = TransactionCodeEnum.FAILED
                    currentPayment.statusDescription = TransactionStatusEnum.FAILED
                    currentPayment.updated_at = datetime.now()
                    paymentQuery.create(db=db,model=currentPayment)
                    logger.info(f"topup failed for {payload.customerNumber} with biller {biller.billerName} at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
    else: 
        logger.info(f"{INSUFFICIENTFUND} with user {user.firstname}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
async def walletEnquiry(
        wallet:str,
        response: Response,
        db: Session,
):
    logger.info(f"Started wallet account enquiry {wallet}")
    walletAccount = queries.queryWallet(db=db,walletAccount=wallet)
    if walletAccount:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=f"{walletAccount.user.firstname} {walletAccount.user.lastname}")
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
async def walletTransfer(
        payload:WalletDebitRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks
):
    try:
        if payload.senderAccount == payload.receiverAccount:
            logger.info(f"{payload.senderAccount} sender and recipient account {payload.receiverAccount} cannot be same at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SAMEACCOUNT)
        if user.wallet.walletAccount != payload.senderAccount:
            logger.info(f"{payload.senderAccount} sender and recipient account {payload.receiverAccount} cannot be same at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription ="Suspected fraudulent transaction")
        recipient = queries.queryWallet(db=db,walletAccount=payload.receiverAccount)
        if not recipient:
            logger.info(f"{payload.receiverAccount} wallet not found")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNTREP)
        logger.info(f"{payload.senderAccount} started payment for biller {payload.billerId} for amount {payload.billerType} at {datetime.now()}")
        productType = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId, billerType=payload.billerType)
        if not productType:
            logger.info(f"Product Type not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        if not productType.provider:
            logger.info(f"{payload.senderAccount} Provider not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        serviceCharge = queries.getServiceProviderByProduct(db=db,productTypeId=productType.id)
        if not serviceCharge:
            logger.info(f"{payload.senderAccount} Service charge not configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
        logger.info(f"{payload.senderAccount}  {serviceCharge.admin.companyName}  is configured configured at {datetime.now()}")
        provider_cost = int(serviceCharge.provider_discount_rate) if serviceCharge.provider_discount_type == CommissionType.calculated else int(payload.amount) * (serviceCharge.provider_discount_rate/100)
        amountToDebit = int(payload.amount) + provider_cost
        if float(user.wallet.availableBalance) < float(amountToDebit):
            logger.info(f"{payload.senderAccount} Insufficient fund to send fund at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = INSUFFICIENTFUND)
        transactionReference = f"W2W-{util.generateId()}"
        creditvalues ={"availableBalance":int(recipient.availableBalance) + int(payload.amount),"updated_at":datetime.now()}
        debitvalues={"availableBalance":int(user.wallet.availableBalance) - int(amountToDebit),"updated_at":datetime.now()}
        db.execute(update(AccountModel).where(AccountModel.id == recipient.id).values(**creditvalues).execution_options(synchronize_session="fetch"))
        db.execute(update(AccountModel).where(AccountModel.id == user.wallet.id).values(**debitvalues).execution_options(synchronize_session="fetch"))
        paymentRecord = [
            PaymentModel(
            wallet_id = user.wallet.id,
            user_id = user.id, 
            amount = int(amountToDebit),
            payment_type = PaymentEnum.DEBIT,
            reference =transactionReference,
            event = "charge.success",
            status = "success",
            channel = ChannelEnum.WALLET,
            providerAmount = provider_cost,
            statusCode = TransactionCodeEnum.SUCCESS,
            statusDescription = TransactionStatusEnum.SUCCESS,
            commissionAmount = 0,
            transactionreference=transactionReference,
            product_type_id = productType.id,
            product_id=productType.product_id,
            provider_code = serviceCharge.admin.billerId,
            recipient=user.wallet.walletAccount, 
            statusMessage = payload.description,
            balanceBefore = user.wallet.availableBalance,
            balanceAfter = user.wallet.availableBalance,
            created_at =datetime.now(),
            updated_at = datetime.now()),
            PaymentModel(
            wallet_id = recipient.id,
            user_id = recipient.user_id, 
            amount = int(payload.amount),
            payment_type = PaymentEnum.CREDIT,
            transactionreference = transactionReference,
            event = "charge.success",
            status = "success",
            channel = ChannelEnum.WALLET,
            providerAmount = provider_cost,
            statusCode = TransactionCodeEnum.SUCCESS,
            statusDescription = TransactionStatusEnum.SUCCESS,
            commissionAmount = 0,
            reference= util.generateId(),
            product_type_id = productType.id,
            product_id=productType.product_id,
            provider_code = serviceCharge.admin.billerId,
            recipient=recipient.walletAccount,
            statusMessage = payload.description,
            balanceBefore = recipient.availableBalance,
            balanceAfter = recipient.availableBalance,
            created_at =datetime.now(),
            updated_at = datetime.now())
        ]
        db.add_all(paymentRecord)
        db.commit()
        process_gl_transactions.delay(transactionReference)
        return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":transactionReference})
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def debitWallet(
        payload:WalletDebitRequest,
        request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Customer,
    sender:AccountModel,
    recipient:AccountModel,
    product:ProductModel,
    background_task:BackgroundTasks
):
    biller = util.find_item(product.billers,"billerId","debit")
    if biller:
        trnxId = f"{str(biller.billerId[:2]).upper()}-{util.generateId()}"
        # debit customer
        logger.info(f"started debit for customer account {sender.walletAccount} at {datetime.now()}")
        sender.availableBalance = int(sender.availableBalance) - int(payload.amount)
        sender.updated_at = datetime.now()
        sender.payments.append(PaymentModel(
            wallet_id = sender.id,user_id =sender.user_id, amount = int(payload.amount),
            payment_type =PaymentEnum.DEBIT,reference =trnxId,
            event = "charge.success",status = "success",channel =ChannelEnum.WALLET,providerAmount = 0,
            statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,
            commissionAmount = 0,transactionreference=trnxId,product_type_id = biller.id,product_id=biller.product_id,
            recipient=sender.walletAccount,statusMessage = payload.description,balanceBefore = sender.availableBalance,
            balanceAfter = sender.availableBalance,created_at =datetime.now(),updated_at = datetime.now())),
        logger.info(f"balance after debit posted successfully is {sender.availableBalance}")
        savedSender = adminQuery.save(db=db,account=sender)
        if savedSender:
            background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
            recipient.availableBalance = int(recipient.availableBalance) + int(payload.amount)
            recipient.updated_at = datetime.now()
            recipient.payments.append(PaymentModel(
                wallet_id = recipient.id,user_id = recipient.user_id,amount = int(payload.amount),
                payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                transactionreference=trnxId,commissionAmount = 0,fee = 0,
                event = "charge.success",status = "success",channel = ChannelEnum.WALLET,
                statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,
                product_type_id = biller.id,product_id=biller.product_id,
                recipient=recipient.walletAccount,statusMessage = payload.description,balanceBefore = recipient.availableBalance,
                balanceAfter =recipient.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
            creditProductType = util.find_item(product.billers,"billerId","credit")
            logger.info(f"create credit record for reciever {recipient.walletAccount} with balance after {recipient.availableBalance}")
            savedRecipient = adminQuery.create(db=db,model=recipient)
            if savedRecipient:
                background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task,user=user)
                return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":trnxId})
            logger.info(f"unable to credit recipient at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
        logger.info(f"unable to debit sender at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
    logger.info(f"service not configured at {datetime.now()}")
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)         
async def debitBusTicket(db:Session,request:Request,response:Response,setting:Setting,payload:BuyTicketRequest,user:CustomerModel,background_task:BackgroundTasks):
    try:
        logger.info(f"Started debit process for bus ticket payment {payload.busId} for amount {payload.amount} for {user.firstname}")
        if user.wallet.walletAccount == payload.walletAccount:
            bus = queries.busById(db=db,busId=payload.busId)
            if bus:
                if bus.availabilityStatus in [BusStatusEnum.BOARDING,BusStatusEnum.ACTIVE,BusStatusEnum.OPEN]:
                    product = adminQuery.getBillerByBillerId(db=db,billerId=bus.billerId)
                    if product:
                        if int(user.wallet.availableBalance) > int(payload.amount):
                            logger.info(f"balance is sufficient {user.wallet.availableBalance}")
                            route = queries.getBusRouteByIdentifier(db=db, routeId=payload.routeId)
                            if route:
                                merchant = adminQuery.getAdminByCustomerId(db=db,id=user.id)
                                return await glAccountingService.debitBusTransaction(request=request,response=response,setting=setting,db=db,biller=product,customer=user,payload=payload,bus=bus,route=route,background_task=background_task,remark=f"{bus.name}/{payload.busId}",merchant=merchant)
                            else:
                                logger.info(f"{ROUTEERROR} with user {user.firstname}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ROUTEERROR)
                        else:
                            logger.info(f"{INSUFFICIENTFUND} with user {user.firstname}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
                    else:
                        logger.info(f"Invalid bus selected {payload.busId} for {user.firstname}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus error biller not found")
                else:
                    logger.info(f"Bus {payload.busId} is not available for {user.firstname}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus currently not available at the moment")
            else:
                logger.info(f"Invalid bus selected {payload.busId} for {user.firstname}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus not found")
        else:
            logger.info(f"Invalid account selected {payload.walletAccount} for {user.firstname}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
async def debitTrainTicket(db:Session,request:Request,response:Response,setting:Setting,payload:BuyTrainTicketRequest,user:CustomerModel,background_task:BackgroundTasks):
    try:
        logger.info(f"Started debit process for train ticket payment {payload.trainId} for amount {payload.amount} for {user.firstname}")
        if user.wallet.walletAccount == payload.walletAccount:
            train = queries.trainById(db=db,trainId=payload.trainId)
            if train:
                logger.info(f"Train is available at {datetime.now()}")
                product = queries.getBillerByBillerId(db=db,billerId=train.billerId)
                if product:
                    logger.info(f"Product is available at {datetime.now()}")
                    seat = queries.seatById(db=db,seatId=payload.seatId)
                    if seat:
                        logger.info(f"pricing is available at {datetime.now()}")
                        route = queries.getRouteByIdentier(db=db,routeId=payload.routeId)
                        if route:
                            logger.info(f"Route is available at {datetime.now()}")
                            schedule = queries.getScheduleById(db=db,scheduleId=payload.scheduleId)
                            if schedule:
                                totalAdult = payload.adult * int(seat.price)
                                totalMinor = payload.minor * int(seat.price)
                                allTotal = totalAdult + totalMinor
                                totalAmount = allTotal
                                if payload.trip == 1:
                                    totalAmount = allTotal * 2
                                if totalAmount == payload.amount:
                                    if int(user.wallet.availableBalance) > int(payload.amount):
                                        logger.info(f"balance is sufficient {user.wallet.availableBalance}")
                                        return await glAccountingService.debitTrainTransaction(request=request,response=response,setting=setting,db=db,biller=product,customer=user,payload=payload,train=train,seat=seat,schedule=schedule,route=route,background_task=background_task)
                                    else:
                                        logger.info(f"{INSUFFICIENTFUND} with user {user.firstname}")
                                        response.status_code = status.HTTP_400_BAD_REQUEST
                                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
                                else:
                                    logger.info(f"Calculated Amount {payload.amount} is not equal for {user.firstname}")
                                    response.status_code = status.HTTP_400_BAD_REQUEST
                                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Price error")
                            else:
                                logger.info(f"schedule {payload.scheduleId} is not available for {user.firstname}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="schedule not available")
                        else:
                            logger.info(f"Route {payload.routeId} is not available for {user.firstname}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Route not available")
                    else:
                        logger.info(f"Seat {payload.seatId} is not available for {user.firstname}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Seat not available")
                else:
                    logger.info(f"Invalid bus selected {payload.trainId} for {user.firstname}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Train error biller not found")
            else: 
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Train not found")
        else:
            logger.info(f"Invalid account selected {payload.walletAccount} for {user.firstname}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
async def redeemTicket(user:Customer,db:Session,request:Request,response:Response,payload:RedeemRequest,setting:Setting,background_task:BackgroundTasks):
    try:
        product = adminQuery.getBillerByBillerId(db=db,billerId=payload.mode)
        if product:
            ticket = queries.ticketByTicketNumber(db=db,mode=TicketModeEnum(payload.mode),ticketId=payload.ticketId)
            if ticket:
                if ticket.status == TicketStatusEnum.BOOKED:
                    logger.info(ticket.expired_at)
                    if ticket.expired_at > datetime.now():
                        if ticket.customer.wallet.walletAccount == payload.walletAccount:
                            if ticket.bus.bus_number == payload.busNumber:
                                return await glAccountingService.redeemTicket(response=response,setting=setting,db=db,biller=product,ticket=ticket,background_task=background_task)

                                ticket.status = TicketStatusEnum.USED
                                ticket.updated_at = datetime.now()
                                updatedTicket = queries.create(db=db,model=ticket)
                                background_task.add_task(notifyUser,db=db,title=f"Redeem Ticket", message=f"Ticket {ticket.ticket_number} Redeemed Successful",userId=ticket.bus.user_id, setting=setting)
                                email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": ticket.bus.user,"ticket":ticket},)
                                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Redeem Ticket",toAddress=ticket.bus.user.email)
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Ticket cannot be use on this bus",)
                    else:
                        ticket.status = TicketStatusEnum.EXPIRED
                        ticket.updated_at = datetime.now()
                        updatedTicket = queries.create(db=db,model=ticket)
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=EXPIREDTICKET,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=ticket.status,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDTICKET,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getAllTickets(request: Request,response: Response,setting: Setting,db: Session,user: Customer,startDate: str=None,endDate: str=None,transactionType: str=None):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate} for {transactionType}"
        )
        if startDate and endDate:
            if transactionType:
                return TicketsResponse(
                    statusCode= str(status.HTTP_200_OK),
                    statusDescription=SUCCESS,
                    data=queries.getTicketsHistoriesByTransaction(db=db,userId=user.id,startDate=startDate,endDate=endDate,transType=transactionType)
                )
            return TicketsResponse(
                    statusCode= str(status.HTTP_200_OK),
                    statusDescription=SUCCESS,
                    data=queries.getTicketHistories(db=db,userId=user.id,startDate=startDate,endDate=endDate)
                )
        return TicketsResponse(
                    statusCode= str(status.HTTP_200_OK),
                    statusDescription=SUCCESS,
                    data=queries.getTicketHistories(db=db,userId=user.id)
                )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def singleTicket(response: Response,db: Session,user: Customer,ticketId: str,mode:str):
    try:
        logger.info(
            f"started querying ticket {ticketId} for {user.email} {TicketModeEnum[mode.upper()]}"
        )
        return TicketResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.ticketByTicketNumber(db=db,mode=TicketModeEnum[mode.upper()],ticketId=ticketId)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
# cashout
async def getbanks(response: Response,setting: Setting):
    try:
        logger.info(
            f"started querying bank list from paystack"
        )
        headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
        result = util.http(f"{setting.paystack_url}bank?currency=NGN",headers=headers)
        if result.status_code == 200:
            paystackResponse = result.json()
            if paystackResponse and paystackResponse["status"] is True:
                banks = paystackResponse.get("data", [])
                if banks:
                    return BaseResponse(
                        statusCode= str(status.HTTP_200_OK),
                        statusDescription=SUCCESS,
                        data=banks)
            response.status_code = status.HTTP_200_OK
            return BaseResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=result.json().get("data", []))
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def verifyCashoutAccount(
        payload:VerifyCashoutRequest,
        response: Response,
        setting: Setting,
        user: CustomerModel,
):
        try:
            logger.info(f"Started cashout account verification process recipient {user.firstname} {user.lastname} for {user.email}")
            headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
            result = util.http(f"{setting.paystack_url}bank/resolve?account_number={payload.accountNumber}&bank_code={payload.bankCode}",headers=headers)
            if result.status_code == 200:
                paystackResponse = result.json()
                if paystackResponse and paystackResponse["status"] is True:
                    recipientData = paystackResponse.get("data", {})
                    if recipientData:
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=recipientData)
                else:
                    logger.info(f"Failed to verify cashout account recipient {user.firstname} {user.lastname} for {user.email}")
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
            else:
                logger.info(f"Failed to verify cashout account recipient {user.firstname} {user.lastname} for {user.email}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json().get('message',"Connection problem"),)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addCashoutRecipient(
        payload:AddCashoutRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks
):
        try:
            logger.info(f"Started adding cashout recipient {user.firstname} {user.lastname} for {user.email}")
            if user.cashout_enabled:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout account already exist",)
            else:
                headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                params ={ "type": "nuban","name":f"{user.firstname} {user.lastname}","account_number": payload.accountNumber,"bank_code": payload.bankCode, "currency": "NGN" }
                result = util.http(f"{setting.paystack_url}transferrecipient",params=params,headers=headers)
                if result.status_code == 201:
                    paystackResponse = result.json()
                    if paystackResponse and paystackResponse["status"] is True:
                        recipientData = paystackResponse.get("data", {})
                        if recipientData:
                            user.cashout_account = recipientData["details"]["account_number"]
                            user.cashout_bank= recipientData["details"]["bank_name"]
                            user.cashout_enabled = True
                            user.cashout_code = recipientData["recipient_code"]
                            user.wallet.cashout_enabled = True
                            user.wallet.cashout_account = payload.accountNumber
                            user.wallet.cashout_code = recipientData.get("recipient_code")
                            user.wallet.cashout_bank = payload.bankCode
                            user.wallet.updated_at = datetime.now()
                            updatedUser = queries.create(db=db,model=user)
                            if updatedUser:
                                background_task.add_task(notifyUser,db=db,title=f"Cashout Recipient Added", message=f"Cashout recipient {user.firstname}{user.lastname} added successfully",userId=user.id, setting=setting)
                                email_debit = util.templates.TemplateResponse("cashout_setup.html",{"request": request, "user": user,"recipient":recipientData},)
                                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Recipient Added",toAddress=user.email)
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESSCASHOUTRECIPIENT)
                    else:
                        logger.info(f"Failed to add cashout recipient {user.firstname} {user.lastname} for {user.email}")
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                else:
                    logger.info(f"Failed to add cashout recipient {user.firstname} {user.lastname} for {user.email}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json()['message'],)
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addCashout(
        payload:CashoutRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks
):
        try:
            logger.info(f"Started adding cashout request of {payload.amount} for {user.firstname} {user.lastname} for {user.email}")
            if user.account_type == AccountEnum.MERCHANT:
                if user.cashout_enabled and user.cashout_code and user.cashout_account and user.cashout_bank:
                    if int(user.cashout_limit) < int(payload.amount):
                        logger.info(f"Cashout limit exceeded  at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription ="Cashout limit exceeded")
                    logger.info(f"{user.wallet.walletAccount} started payment for biller {payload.billerId} for amount {payload.billerType} at {datetime.now()}")
                    productType = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId, billerType=payload.billerType)
                    if not productType:
                        logger.info(f"Product Type not configured at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
                    if not productType.provider:
                        logger.info(f"{user.wallet.walletAccount} Provider not configured at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
                    serviceCharge = queries.getServiceProviderByProduct(db=db,productTypeId=productType.id)
                    if not serviceCharge:
                        logger.info(f"{user.wallet.walletAccount} Service charge not configured at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
                    logger.info(f"{user.wallet.walletAccount}  {serviceCharge.admin.companyName}  is configured configured at {datetime.now()}")
                    provider_cost = int(serviceCharge.provider_discount_rate) if serviceCharge.provider_discount_type == CommissionType.calculated else int(payload.amount) * (serviceCharge.provider_discount_rate/100)
                    amountToDebit = int(payload.amount) + provider_cost
                    if int(user.wallet.availableBalance) >= int(payload.amount):
                        logger.info(f"balance is sufficient {user.wallet.availableBalance}  @ {datetime.now()}")
                        dailyCashout = int(payload.amount)
                        cashOutDailyLimit = queries.getDailyCashoutTransactionsByUser(db=db,productId=productType.id,userId=user.id)
                        logger.info(cashOutDailyLimit)
                        if cashOutDailyLimit:
                                dailyCashout = int(cashOutDailyLimit) + dailyCashout
                        if dailyCashout > int(user.cashout_limit):
                            logger.info(f"Cashout limit exceeded  at {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription ="Cummulative cashout limit exceeded") 
                        trnxId = f"CSH-{util.generateId()}"
                        logger.info(f"cash out is below user limit {user.cashout_limit}  @ {datetime.now()}")
                        logger.info(f"cash out is below user limit {dailyCashout}  @ {datetime.now()}")
                        newBalance = int(user.wallet.availableBalance) - int(payload.amount)
                        debitvalues={"availableBalance":newBalance,"updated_at":datetime.now()}
                        db.execute(update(AccountModel).where(AccountModel.id == user.wallet.id).values(**debitvalues).execution_options(synchronize_session="fetch"))
                        paymentRecord = [
                            PaymentModel(
                                wallet_id = user.wallet.id,
                                user_id =user.id,
                                amount = payload.amount,
                                payment_type =PaymentEnum.DEBIT,
                                reference = trnxId,
                                event = "charge.processing",
                                status = "started",
                                channel = ChannelEnum.WEB,
                                transactionreference = trnxId,
                                providerAmount = provider_cost,
                                statusCode = TransactionCodeEnum.PROCESSING,
                                statusDescription = TransactionStatusEnum.PROCESSING,
                                recipient=user.cashout_account,
                                statusMessage = f"Cashout to {user.cashout_account} {user.cashout_bank}",
                                balanceBefore = user.wallet.availableBalance,
                                balanceAfter = newBalance,
                                product_id=productType.product_id,
                                product_type_id=productType.id,  # Assuming product_id is 1 for cashout
                                cashout = CashOutModel(
                                    user_id = user.id,
                                    source= 'balance',
                                    amount= payload.amount,
                                    recipient= user.cashout_code,
                                    withdrawalStatus = WithrawalStatusEnum.WAITING,
                                    statusCode = TransactionCodeEnum.PROCESSING,
                                    statusDescription = TransactionStatusEnum.PROCESSING,
                                    reference = trnxId,
                                    reason = payload.desc,
                                    created_at = datetime.now(),
                                    updated_at =  datetime.now()
                                ),
                                created_at =datetime.now(),
                                updated_at = datetime.now()
                            )
                        ]
                        db.add_all(paymentRecord)
                        db.commit()
                        process_cashout_payment.delay(transactionReference=trnxId)
                        return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":trnxId})
                    else:
                        logger.info(f"Insufficient balance for {user.email} to cashout @ {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
                else:
                    logger.info(f"Cashout not enabled for {user.firstname} {user.lastname} for {user.email} @ {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout not enabled or invalid recipient details")
            else:
                logger.info(f" {user.email} is not eligible for cashout transactions @ {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout not enabled or invalid recipient details")
        except Exception as ex:
            logger.info(ex)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def get_trip_seats(trip_id: int, db: Session):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()

    seats = db.query(Seat).filter(
        Seat.bus_type_id == trip.bus.bus_type_id
    ).all()

    booked = db.query(Booking.seat_id).filter(
        Booking.trip_id == trip_id,
        Booking.status.in_([TicketStatusEnum.BOOKED, TicketStatusEnum.EXPIRED])
    ).all()

    booked_ids = {b[0] for b in booked}

    result = []

    for seat in seats:
        result.append({
            "id": str(seat.id),
            "label": seat.seat_label,
            "row": seat.row,
            "column": seat.column,
            "status": "BOOKED" if seat.id in booked_ids else "AVAILABLE"
        })

    return result
# Admin Payments
def adminPayments(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            payments=queries.getAllPaymentsHistories(db=db,startDate=startDate,endDate=endDate)
        else:
            payments=queries.getAllPaymentsHistories(db=db,adminId=admin.id,startDate=startDate,endDate=endDate)
        return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=[Payment.from_orm(payment).model_dump() for payment in payments]
                
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def listOfCashout(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return CashoutsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getListOfcashout(db=db,startDate=startDate,endDate=endDate)
            )
        else:
            return CashoutsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getListOfcashout(db=db,adminId=admin.id,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CashoutsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
