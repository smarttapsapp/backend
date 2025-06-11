
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import paymentQuery,queries
from datetime import datetime,timedelta
from schemas import otp
from utils import util
from schemas.setting import Setting
from services.notificationservice import notifyUser
from utils.constant import *
from schemas.customer import *
from schemas.payment import *
from schemas.ticket import TicketResponse,TicketsResponse
from schemas.admin import Admin
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
                message = f'You have setup auto fund of ₦{util.kobo_to_naira(payload.amount):,.2f} for your purse with a threshold of ₦{util.kobo_to_naira(payload.thresholdAmount):,.2f} at {datetime.now().strftime("%B %d, %Y %I:%M %p")}'
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

def fundViaPaystack(
        user:Customer,
        request: Request,
        db: Session,
        response: Response,
        setting: Setting,amount:str):
    try:
        product = queries.getBillByVas(db=db,vasType="payment")
        if product:
            creditProductType = util.find_item(product.billers,"billerId","credit")
            if creditProductType:
                payment = PaymentModel(
                    wallet_id = user.wallet.id,
                    user_id = user.id,
                    amount = amount,
                    channel = "PAYSTACK",
                    product_type_id = creditProductType.id,
                    product_id=product.id,
                    recipient=user.wallet.walletAccount,
                    payment_type = PaymentEnum.CREDIT,
                    created_at = datetime.now(),
                    updated_at= datetime.now(),
                )
                createdPayment = paymentQuery.create_payment(db=db,payment=payment)
                appResponse = None
                if createdPayment:
                    headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                    params = {"email": user.email,"amount": amount}
                    result = util.http(setting.paystack_url,params=params,headers=headers)
                    logger.info(result)
                    if result.status_code == 200:
                        paystackResponse = result.json()
                        if paystackResponse and paystackResponse["status"] is True:
                            createdPayment.reference = paystackResponse["data"]["reference"]
                            createdPayment.access_code = paystackResponse["data"]["access_code"]
                            createdPayment.statusCode = str(status.HTTP_200_OK)
                            createdPayment.statusMessage = paystackResponse["message"]
                            appResponse = BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=paystackResponse["message"],data=paystackResponse["data"])
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            createdPayment.statusCode = str(status.HTTP_400_BAD_REQUEST)
                            createdPayment.statusMessage = paystackResponse["message"]
                            appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse["message"])
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        createdPayment.statusCode = str(status.HTTP_400_BAD_REQUEST)
                        createdPayment.statusMessage = "Failed"
                        appResponse = BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
                    createdPayment.event = "initialize"
                    updatePayment = paymentQuery.create_payment(db=db,payment=createdPayment)
                    if updatePayment:
                        return appResponse
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Failed")
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
async def fundNotificationViaPaystack(
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
            payment.event = json_data["event"]
            payment.channel = json_data["data"]["channel"]
            payment.payment_date = json_data["data"]["channel"]
            payment.status = json_data["data"]["status"]
            payment.fee = json_data["data"]["fees"]
            payment.paystack_id = json_data["data"]["id"]
            payment.payment_date = json_data["data"]["paid_at"]
            payment.balanceBefore = payment.wallet.availableBalance
            payment.balanceAfter = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
            payment.wallet.availableBalance = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
            payment.updated_at = datetime.now()
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
                background_task.add_task(notifyUser,db=db,title=f"Fund Notification", message=updatedPayment.statusMessage,userId=payment.user_id, setting=setting)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to add fund",)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def payments(request: Request,response: Response,setting: Setting,db: Session,user: Customer,startDate: str,endDate: str,transactionType: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate} for {transactionType}"
        )
        if transactionType:
            return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getPaymentHistoriesByTransaction(db=db,userId=user.id,startDate=startDate,endDate=endDate,transType=transactionType)
            )
        return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getPaymentHistories(db=db,userId=user.id,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def getSinglePayment(
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
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(
               statusCode=str(status.HTTP_400_BAD_REQUEST),
               statusDescription=UNKNOWNTRANSACTION,
        )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentResponse(
               statusCode=str(status.HTTP_400_BAD_REQUEST),
               statusDescription=SYSTEMBUSY,
        )
def payment(
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
def nfcdebitService(
        payload:DebitRequest,
        request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Customer,
    background_task:BackgroundTasks
):
    try:
        logger.info(f"started debit transaction via NFC for sender {payload.senderAccount} to receiver {payload.walletAccount}")
        sender = paymentQuery.querySender(db=db,walletAccount=payload.senderAccount)
        if sender:
            verifiedPIN = util.verify_password(payload.pin,sender.user.pin)
            if verifiedPIN:
                if payload.senderAccount != user.wallet.walletAccount:
                    duplicate = paymentQuery.getPaymentByReference(db=db,reference=payload.transactionId)
                    if duplicate:
                        logger.info(f"duplicate transaction found {duplicate.reference}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=DUPLICATE)
                    else:
                        product = queries.getBillByVas(db=db,vasType="payment")
                        if product:
                            if float(sender.availableBalance) >= float(payload.amount):
                                lastTransaction = paymentQuery.queryLatestRecordByAmount(db=db,amount=payload.amount)
                                if lastTransaction:
                                    logger.info(f"last transaction from sender {payload.senderAccount} is {lastTransaction.created_at}")
                                    timeDifference  = (datetime.now() - lastTransaction.updated_at).total_seconds()
                                    logger.info(f"ths time difference is {timeDifference}")
                                    if int(timeDifference) > 5:
                                        #if lastTransaction.amount != payload.amount:
                                        #    lastTransactionTime = datetime.strptime(lastTransaction.updated_at, "%Y-%m-%d %H:%M:%S")
                                        return debitNfc(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,product=product,background_task=background_task)
                                        #else:
                                        #    response.status_code = status.HTTP_400_BAD_REQUEST
                                        #    return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = DUPLICATE)
                                    else:
                                        response.status_code = status.HTTP_400_BAD_REQUEST
                                        return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = DUPLICATE)
                                else:
                                    return debitNfc(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,product=product,background_task=background_task)
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = INSUFFICIENTFUND)
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
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
        return PaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
def debitNfc(
        payload:DebitRequest,
        request: Request,
    response: Response,
    setting: Setting,
    db: Session,
    user: Customer,
    sender:AccountModel,
    product:ProductModel,
    background_task:BackgroundTasks
):
    debitProductType = util.find_item(product.billers,"billerId","debit")
    if debitProductType:
        sender.availableBalance = (int(sender.availableBalance) - int(payload.amount))
        updatedAccount = paymentQuery.create(db=db,model=sender)
        logger.info(f"balance after debit posted successfully is {updatedAccount.availableBalance}")
        if updatedAccount:
            debit = PaymentModel(
            wallet_id = sender.id,
            user_id =sender.user_id,
            amount = payload.amount,
            payment_type =PaymentEnum.DEBIT,
            reference =payload.transactionId,
            event = "charge.success",
            status = "success",
            channel = "NFC",
            fee = "1000",
            payment_date = datetime.now().date(),
            statusCode = "200",
            product_type_id = debitProductType.id,
            product_id=product.id,
            recipient=user.wallet.walletAccount,
            statusMessage = payload.description,
            balanceBefore = sender.availableBalance,
            balanceAfter = updatedAccount.availableBalance,
            created_at =datetime.now(),
            updated_at = datetime.now()
            )
            createDebitRecord = paymentQuery.create(db=db,model=debit)
            if createDebitRecord:
                background_task.add_task(notifyUser,db=db,title=f"Debit Notification", message=createDebitRecord.statusMessage,userId=user.id, setting=setting)
                email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"payment":createDebitRecord},)
                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Debit Notification",toAddress=user.email)
                logger.info(f"start credit to receiver {user.wallet.walletAccount} with balance before {user.wallet.availableBalance}")
                newBalance =  int(user.wallet.availableBalance)+int(payload.amount)
                updatedReceiver = paymentQuery.updateAccountBalance(db=db,walletId=user.wallet.walletAccount,newBalance=newBalance)
                if updatedReceiver:
                    logger.info(f"create credit record for reciever {user.wallet.walletAccount} with balance after {user.wallet.availableBalance}")
                    creditProductType = util.find_item(product.billers,"billerId","credit")
                    credit = PaymentModel(
                        wallet_id = user.wallet.id,
                        user_id =user.id,
                        amount = payload.amount,
                        payment_type =PaymentEnum.CREDIT,
                        reference =payload.transactionId,
                        event = "charge.success",
                        status = "success",
                        payment_date = datetime.now().date(),
                        channel = payload.transactionChannel,
                        statusCode = "200",
                        product_id=product.id,
                        recipient=sender.walletAccount,
                        product_type_id = creditProductType.id if creditProductType else 1,
                        statusMessage = payload.description,
                        balanceBefore = user.wallet.availableBalance,
                        balanceAfter = updatedReceiver.availableBalance,
                        created_at =datetime.now(),
                        updated_at = datetime.now()
                        )
                    createCreditRecord = paymentQuery.create(db=db,model=credit)
                    if createCreditRecord:
                        background_task.add_task(notifyUser,db=db,title=f"Credit Notification", message=createCreditRecord.statusMessage,userId=user.id, setting=setting)
                        email_credit = util.templates.TemplateResponse("credit.html",{"request": request, "user": user,"payment":createCreditRecord},)
                        background_task.add_task(util.mailer,str(email_credit.body, "utf-8"),setting=setting,subject="Credit Notification",toAddress=user.email)
                        return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":createCreditRecord.reference})
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)    
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)          
def billerEnquiry(
        payload:BillNameEnquiryRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: Customer
):
    biller = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId)
    if payload.customerNumber:
        if biller:
            package = next((x for x in biller.packages if x.packageCode == payload.packageId), None)
            if package:
                if biller.billerType == "utility":
                    return BillNameEnquiryResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={
                        "fullName":"John Doe",
                        "address":"3, lokoja street Abuja Lagos",
                        "minimumAmount":"1000"
                    })
                return BillNameEnquiryResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={
                        "fullName":"John Doe"
                    })
            logger.info(f"Invalid package code selected {payload.packageId}")    
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
        logger.info(f"Invalid biller selected {payload.billerId}")    
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INCOMPLETE)
def payBills(
        payload:BillPaymentRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks
):
    biller = paymentQuery.get_single_biller_by_billerId(db=db,billerId=payload.billerId)
    if payload.customerNumber:
        if biller:
            if biller.hasPackages:
                package = next((x for x in biller.packages if x.packageCode == payload.packageId), None)
                if package:
                    return debitBillPayment(biller=biller,package=package,payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
                else:
                    logger.info(f"Invalid package code selected {payload.packageId}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
            else:
                return debitBillPayment(biller=biller,payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
        logger.info(f"Invalid biller selected {payload.billerId}")    
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INCOMPLETE)
def debitBillPayment(
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
    #amount = int(float(payload.amount) * 100)
    if int(user.wallet.availableBalance) > int(payload.amount):
        logger.info(f"balance is sufficient {user.wallet.availableBalance}")
        newBalance = int(user.wallet.availableBalance) - int(payload.amount)
        user.wallet.availableBalance = newBalance
        updatedUser = paymentQuery.create(db=db,model=user)
        if updatedUser:
            logger.info(f"Start processing payment records ...............")
            debit = PaymentModel(
                wallet_id = user.wallet.id,
                user_id =user.id,
                amount = payload.amount,
                recipient=payload.customerNumber,
                payment_type =PaymentEnum.DEBIT,
                reference =f"{biller.billerName[:3]}-{util.generateId()}",
                event = "charge.success",
                status = "success",
                #payment_date = datetime.now().fromisoformat(),
                channel = "MOBILE",
                fee = "1000",
                statusCode = "200",
                statusMessage = f"{biller.billerType}/{biller.billerName}/{package.packageCode if package else ''}/{payload.customerNumber}",
                balanceBefore = user.wallet.availableBalance,
                balanceAfter = newBalance,
                product_id = biller.product_id,
                product_type_id = biller.id,
                created_at =datetime.now(),
                updated_at = datetime.now()
        )
            createDebitRecord = paymentQuery.create(db=db,model=debit)
            if createDebitRecord:
                background_task.add_task(notifyUser,db=db,title=f"Debit Notification", message=createDebitRecord.statusMessage,userId=user.id, setting=setting)
                email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"payment":createDebitRecord},)
                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Debit Notification",toAddress=user.email)
                logger.info(f"start credit to receiver {user.wallet.walletAccount} with balance before {user.wallet.availableBalance}")
                return BillPaymentResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":createDebitRecord.reference})
    else: 
        logger.info(f"{INSUFFICIENTFUND} with user {user.firstname}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
def walletEnquiry(
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
def walletTransfer(
        payload:WalletDebitRequest,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: CustomerModel,
        background_task:BackgroundTasks
):
    if payload.senderAccount != payload.receiverAccount:
        recipient = queries.queryWallet(db=db,walletAccount=payload.receiverAccount)
        if recipient:
            sender = queries.queryWallet(db=db,walletAccount=payload.senderAccount)
            if sender:
                bill = queries.getBillByVas(db=db,vasType="payment")
                if bill:
                    if float(sender.availableBalance) >= float(payload.amount):
                        lastPayment = queries.getLastpaymentByAccount(db=db,accountId=sender.id)
                        if lastPayment:
                            logger.info(f"last transaction from sender {payload.senderAccount} is {lastPayment.created_at}")
                            timeDifference  = (datetime.now() - lastPayment.updated_at).total_seconds()
                            if timeDifference > 5:
                                return debitWallet(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,recipient=recipient,product=bill,background_task=background_task)
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = DUPLICATE)
                        else:
                            logger.info(f"last payment not found for {sender.walletAccount}")
                            return debitWallet(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,recipient=recipient,product=bill,background_task=background_task)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = INSUFFICIENTFUND)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = SERVICEERROR)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNTREP)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SAMEACCOUNT,)
def debitWallet(
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
    debitProductType = util.find_item(product.billers,"billerId","debit")
    if debitProductType:
        sender.availableBalance = (int(sender.availableBalance) - int(payload.amount))
        updatedAccount = paymentQuery.create(db=db,model=sender)
        logger.info(f"balance after debit posted successfully is {updatedAccount.availableBalance}")
        if updatedAccount:
            debit = PaymentModel(
            wallet_id = sender.id,
            user_id =sender.user_id,
            amount = int(payload.amount*100),
            payment_type =PaymentEnum.DEBIT,
            reference =f"TRF-{util.generateUniqueId()}",
            event = "charge.success",
            payment_date = datetime.now().date(),
            status = "success",
            channel = "WALLET",
            fee = "1000",
            statusCode = "200",
            product_type_id = debitProductType.id,
            product_id=product.id,
            recipient=recipient.walletAccount,
            statusMessage = payload.description,
            balanceBefore = sender.availableBalance,
            balanceAfter = updatedAccount.availableBalance,
            created_at =datetime.now(),
            updated_at = datetime.now()
            )
            createDebitRecord = paymentQuery.create(db=db,model=debit)
            if createDebitRecord:
                background_task.add_task(notifyUser,db=db,title=f"Debit Notification", message=createDebitRecord.statusMessage,userId=user.id, setting=setting)
                email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"payment":createDebitRecord},)
                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Debit Notification",toAddress=user.email)
                logger.info(f"start credit to receiver {user.wallet.walletAccount} with balance before {user.wallet.availableBalance}")
                recipient.availableBalance =  int(recipient.availableBalance)+int(payload.amount)
                updatedReceiver = queries.create(db=db,model=recipient)
                logger.info(f"balance after credit posted successfully is {updatedReceiver.availableBalance}")
                if updatedReceiver:
                    logger.info(f"create credit record for reciever {recipient.walletAccount} with balance after {recipient.availableBalance}")
                    creditProductType = util.find_item(product.billers,"billerId","credit")
                    credit = PaymentModel(
                        wallet_id = recipient.id,
                        user_id =recipient.user_id,
                        amount = int(payload.amount*100),
                        payment_type =PaymentEnum.CREDIT,
                        reference =f"TRF-{util.generateUniqueId()}",
                        event = "charge.success",
                        status = "success",
                        payment_date = datetime.now().date(),
                        channel ="WALLET",
                        statusCode = "200",
                        product_id=product.id,
                        product_type_id = creditProductType.id if creditProductType else 1,
                        recipient=recipient.walletAccount,
                        statusMessage = payload.description,
                        balanceBefore = recipient.availableBalance,
                        balanceAfter = updatedReceiver.availableBalance,
                        created_at =datetime.now(),
                        updated_at = datetime.now()
                        )
                    createCreditRecord = queries.create(db=db,model=credit)
                    if createCreditRecord:
                        background_task.add_task(notifyUser,db=db,title=f"Credit Notification", message=createCreditRecord.statusMessage,userId=user.id, setting=setting)
                        email_credit = util.templates.TemplateResponse("credit.html",{"request": request, "user": user,"payment":createCreditRecord},)
                        background_task.add_task(util.mailer,str(email_credit.body, "utf-8"),setting=setting,subject="Credit Notification",toAddress=user.email)
                        return BaseResponse(statusCode="00",statusDescription=SUCCESS,data={"transactionId":createDebitRecord.reference})
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)   
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)            
def debitBusTicket(db:Session,request:Request,response:Response,setting:Setting,payload:BuyTicketRequest,user:CustomerModel,background_task:BackgroundTasks):
    try:
        logger.info(f"Started debit process for bus ticket payment {payload.busId} for amount {payload.amount} for {user.firstname}")
        if user.wallet.walletAccount == payload.walletAccount:
            bus = queries.busById(db=db,busId=payload.busId)
            if bus:
                if bus.availabilityStatus:
                    if int(user.wallet.availableBalance) > int(payload.amount):
                        logger.info(f"balance is sufficient {user.wallet.availableBalance}")
                        newBalance = int(user.wallet.availableBalance) - int(payload.amount)
                        user.wallet.availableBalance = newBalance
                        updatedUser = paymentQuery.create(db=db,model=user)
                        if updatedUser:
                            logger.info(f"Start processing payment records ...............")
                            debit = PaymentModel(
                                wallet_id = user.wallet.id,
                                user_id =user.id,
                                amount = payload.amount,
                                payment_type =PaymentEnum.DEBIT,
                                reference =f"BUS-{util.generateId()}",
                                event = "charge.success",
                                status = "success",
                                channel = "MOBILE",
                                fee = "1000",
                                statusCode = "200",
                                statusMessage = f"{bus.name}/{bus.park.name}/{payload.busId}",
                                balanceBefore = user.wallet.availableBalance,
                                balanceAfter = newBalance,
                                created_at =datetime.now(),
                                updated_at = datetime.now()
                            )
                            createDebitRecord = paymentQuery.create(db=db,model=debit)
                            if createDebitRecord:
                                ticketId =  f"BUS-{util.generateId()}"
                                logger.info(f"create ticket record for bus {payload.busId} with balance after {user.wallet.availableBalance} ticket reference is {ticketId}")
                                ticket = TicketModel(
                                    bus_id = bus.id,
                                    customer_id = user.id,
                                    route_id = bus.route_id,
                                    schedule_id = payload.scheduleId,
                                    qr_code = f"{ticketId}|{bus.bus_number}|{TicketModeEnum.BUS.value}|{user.wallet.walletAccount}",
                                    mode = TicketModeEnum.BUS,
                                    price = payload.amount,
                                    ticket_number = ticketId,
                                    booked_at =datetime.now(),
                                    created_at =datetime.now(),
                                    updated_at = datetime.now()
                                )
                                createTicketRecord = paymentQuery.create(db=db,model=ticket)
                                background_task.add_task(notifyUser,db=db,title=f"Bus Ticket Purchase", message=createDebitRecord.statusMessage,userId=user.id, setting=setting)
                                email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"payment":createDebitRecord},)
                                background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Bus Ticket Purchase",toAddress=user.email)
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":createTicketRecord.ticket_number})
                    else:
                        logger.info(f"{INSUFFICIENTFUND} with user {user.firstname}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
                else:
                    logger.info(f"Bus {payload.busId} is not available for {user.firstname}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Bus not available")
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
def redeemTicket(user:Customer,db:Session,request:Request,response:Response,payload:RedeemRequest,setting:Setting,background_task:BackgroundTasks):
    try:
        ticket = queries.ticketByTicketNumber(db=db,mode=TicketModeEnum[payload.mode],ticketId=payload.ticketId)
        if ticket:
            if ticket.status == TicketStatusEnum.BOOKED:
                if ticket.expired_at > datetime.now():
                    if ticket.customer.wallet.walletAccount == payload.walletAccount:
                        if ticket.bus.bus_number == payload.busNumber:
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
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def getAllTickets(request: Request,response: Response,setting: Setting,db: Session,user: Customer,startDate: str,endDate: str,transactionType: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate} for {transactionType}"
        )
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
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TicketsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def singleTicket(response: Response,db: Session,user: Customer,ticketId: str,mode:str):
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
def adminPayments(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate}"
        )
        if admin.role.tag == AdminRoleEnum.BUSINESS:
            return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getPaymentHistories(db=db,userId=admin.id,startDate=startDate,endDate=endDate)
            )
        else:
            return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getAllPaymentsHistories(db=db,startDate=startDate,endDate=endDate)
            )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PaymentsResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
