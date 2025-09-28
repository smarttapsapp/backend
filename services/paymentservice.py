
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import paymentQuery,queries,adminQuery
from datetime import datetime,timedelta
from schemas import otp
from utils import util
from schemas.setting import Setting
from services.notificationservice import notifyUser
from services import glAccountingService
from utils.constant import *
from schemas.customer import *
from schemas.payment import *
from schemas.cashout import *
from services import notificationservice,glAccountingService
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
            logger.info(f"I want to check......at {datetime.now()}")
            user.updated_at = datetime.now()
            saved = queries.create(db=db,model=user)
            logger.info(f"I saved to db......at {datetime.now()}")
            if saved:
                message = f"You have setup auto fund of ₦{util.kobo_to_naira(int(payload.amount)):,.2f} for your purse with a threshold of ₦{util.kobo_to_naira(int(payload.thresholdAmount)):,.2f} at "
                logger.info(message)
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
                    channel = ChannelEnum.PAYSTACK,
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
                    result = util.http(f"{setting.paystack_url}transaction/initialize",params=params,headers=headers)
                    if result.status_code == 200:
                        paystackResponse = result.json()
                        if paystackResponse and paystackResponse["status"] is True:
                            createdPayment.reference = paystackResponse["data"]["reference"]
                            createdPayment.access_code = paystackResponse["data"]["access_code"]
                            createdPayment.statusCode = TransactionCodeEnum.PROCESSING
                            createdPayment.statusDescription = TransactionStatusEnum.PROCESSING
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
        headOffice = queries.getHeadofficeAccount(db=db)
        if headOffice:
            payment = paymentQuery.getPaymentByReference(db=db,reference=json_data["data"]["reference"])
            if payment:
                payment.event = json_data["event"]
                payment.channel = json_data["data"]["channel"]
                payment.payment_date = json_data["data"]["channel"]
                payment.status = json_data["data"]["status"]
                payment.fee = json_data["data"]["fees"]
                payment.paystack_id = json_data["data"]["id"]
                payment.payment_date = json_data["data"]["paid_at"]
                payment.statusCode = TransactionCodeEnum.SUCCESS
                payment.statusDescription = TransactionStatusEnum.SUCCESS
                payment.balanceBefore = payment.wallet.availableBalance
                payment.balanceAfter = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
                payment.wallet.availableBalance = str(int(payment.wallet.availableBalance)+int(json_data["data"]["amount"]))
                payment.updated_at = datetime.now()
                payment.wallet.updated_at = datetime.now()
                payment.code = setting.gl_outflow
                payment.user.hasAuthToken = True
                updatedPayment = paymentQuery.create_payment(db=db,payment=payment)
                if updatedPayment:
                    headOffice.wallet.availableBalance = str(int(headOffice.wallet.availableBalance)+int(json_data["data"]["amount"]))
                    headOffice.updated_at = datetime.now()
                    headOffice.wallet.updated_at = datetime.now()
                    headOffice.wallet.payments.append(PaymentModel(wallet_id=headOffice.wallet.id,admin_id=headOffice.id,amount = int(json_data["data"]["amount"]),
                                    payment_type =PaymentEnum.CREDIT,reference =f"FUND-{util.generateId()}",code=setting.gl_inflow,
                                    transactionreference=payment.reference,event = "charge.success",status = "success",channel =ChannelEnum.PAYSTACK,
                                    fee = 0,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,
                                    product_type_id = payment.product_type_id,product_id=payment.product_id,recipient=headOffice.wallet.walletAccount,
                                    statusMessage = payment.statusMessage,balanceBefore =headOffice.wallet.availableBalance,
                                    balanceAfter =headOffice.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                    updatedHeadOfficeCredit = queries.create(db=db,model=headOffice)
                    if updatedHeadOfficeCredit:
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
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=PENDING,)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to add fund",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Config Error",)
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
async def nfcdebitService(
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
                                        return await debitNfc(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,recipient=user.wallet,product=product,background_task=background_task)
                                        #else:
                                        #    response.status_code = status.HTTP_400_BAD_REQUEST
                                        #    return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = DUPLICATE)
                                    else:
                                        response.status_code = status.HTTP_400_BAD_REQUEST
                                        return PaymentResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = DUPLICATE)
                                else:
                                    return await debitNfc(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,recipient=user.wallet,product=product,background_task=background_task)
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
async def debitNfc(
        payload:DebitRequest,
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
            event = "charge.success",status = "success",channel =ChannelEnum.NFC,providerAmount = 0,
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
async def billerEnquiry(
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
async def payBills(
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
                    return await debitBillPayment(biller=biller,package=package,payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
                else:
                    logger.info(f"Invalid package code selected {payload.packageId}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
            else:
                return await debitBillPayment(biller=biller,payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
        logger.info(f"Invalid biller selected {payload.billerId}")    
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INCOMPLETE)
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
        merchant = adminQuery.getAdminByCustomerId(db=db,id=user.id)
        statusMessage = f"{biller.billerType}/{biller.billerName}/{package.packageCode if package else ''}/{payload.customerNumber}"
        return await glAccountingService.debitTransaction(response=response,setting=setting,db=db,biller=biller,customerAccount=user.wallet,amount=int(payload.amount),background_task=background_task,remark=statusMessage,merchant=merchant)
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
    if payload.senderAccount != payload.receiverAccount:
        recipient = queries.queryWallet(db=db,walletAccount=payload.receiverAccount)
        if recipient:
            sender = queries.queryWallet(db=db,walletAccount=payload.senderAccount)
            if sender:
                bill = queries.getBillByVas(db=db,vasType="payment")
                if bill:
                    if int(sender.availableBalance) >= int(payload.amount):
                        lastPayment = queries.getLastpaymentByAccount(db=db,accountId=sender.id)
                        if lastPayment:
                            logger.info(f"last transaction from sender {payload.senderAccount} is {lastPayment.created_at}")
                            timeDifference  = (datetime.now() - lastPayment.updated_at).total_seconds()
                            if timeDifference > 5:
                                return await debitWallet(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,recipient=recipient,product=bill,background_task=background_task)
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode =str(status.HTTP_400_BAD_REQUEST),statusDescription = DUPLICATE)
                        else:
                            logger.info(f"last payment not found for {sender.walletAccount}")
                            return await debitWallet(payload=payload,request=request,response=response,setting=setting,db=db,user=user,sender=sender,recipient=recipient,product=bill,background_task=background_task)
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
                if bus.availabilityStatus:
                    product = adminQuery.getBillerByBillerId(db=db,billerId=bus.billerId)
                    if product:
                        if int(user.wallet.availableBalance) > int(payload.amount):
                            logger.info(f"balance is sufficient {user.wallet.availableBalance}")
                            merchant = adminQuery.getAdminByCustomerId(db=db,id=user.id)
                            return await glAccountingService.debitBusTransaction(request=request,response=response,setting=setting,db=db,biller=product,customer=user,payload=payload,bus=bus,background_task=background_task,remark=f"{bus.name}/{payload.busId}",merchant=merchant)
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
async def debitTrainTicket(db:Session,request:Request,response:Response,setting:Setting,payload:BuyTrainTicketRequest,user:CustomerModel,background_task:BackgroundTasks):
    try:
        logger.info(f"Started debit process for train ticket payment {payload.trainId} for amount {payload.amount} for {user.firstname}")
        if user.wallet.walletAccount == payload.walletAccount:
            train = queries.trainById(db=db,trainId=payload.trainId)
            if train:
                product = queries.getBillerByBillerId(db=db,billerId=train.billerId)
                if product:
                    seat = queries.seatById(db=db,seatId=payload.seatId)
                    if seat:
                        route = queries.getRouteById(db=db,routeId=payload.routeId)
                        if route:
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
            headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
            params ={ "type": "nuban","name":f"{user.firstname} {user.lastname}","account_number": payload.accountNumber,"bank_code": payload.bankCode, "currency": "NGN" }
            result = util.http(f"{setting.paystack_url}transferrecipient",params=params,headers=headers)
            if result.status_code == 201:
                paystackResponse = result.json()
                if paystackResponse and paystackResponse["status"] is True:
                    recipientData = paystackResponse.get("data", {})
                    if recipientData:
                        user.wallet.cashout_enabled = True
                        user.wallet.cashout_account = payload.accountNumber
                        user.wallet.cashout_code = recipientData.get("recipient_code")
                        user.wallet.cashout_bank = payload.bankCode
                        updatedUser = queries.create(db=db,model=user)
                        if updatedUser:
                            background_task.add_task(notifyUser,db=db,title=f"Cashout Recipient Added", message=f"Cashout recipient {user.firstname}{user.lastname} added successfully",userId=user.id, setting=setting)
                            email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"recipient":recipientData},)
                            background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Recipient Added",toAddress=user.email)
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
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
                headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                params ={ "type": "nuban","name":f"{user.firstname} {user.lastname}","account_number": payload.accountNumber,"bank_code": payload.bankCode, "currency": "NGN" }
                result = util.http(f"{setting.paystack_url}transferrecipient",params=params,headers=headers)
                if result.status_code == 201:
                    paystackResponse = result.json()
                    if paystackResponse and paystackResponse["status"] is True:
                        recipientData = paystackResponse.get("data", {})
                        if recipientData:
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
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        logger.info(f"Failed to add cashout recipient {user.firstname} {user.lastname} for {user.email}")
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=paystackResponse['message'],)
                else:
                    logger.info(f"Failed to add cashout recipient {user.firstname} {user.lastname} for {user.email}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=result.json()['message'],)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout account already exist",)
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
                    cashoutPd = queries.getProductTypeBYname(db=db,name="cashout")
                    if cashoutPd:
                        if int(user.wallet.availableBalance) >= int(payload.amount):
                            logger.info(f"balance is sufficient {user.wallet.availableBalance}  @ {datetime.now()}")
                            dailyCashout = 0
                            dailyLimit = queries.getDailyCashoutTransactionsByUser(db=db,productId=cashoutPd.id,userId=user.id)
                            if dailyLimit:
                                dailyCashout = dailyLimit
                            trnxId = f"CASH-{util.generateId()}"
                            logger.info(f"cash out is below user limit {user.cashout_limit}  @ {datetime.now()}")
                            logger.info(f"cash out is below user limit {dailyCashout}  @ {datetime.now()}")
                            newBalance = int(user.wallet.availableBalance) - int(payload.amount)
                            user.wallet.availableBalance = newBalance
                            user.wallet.payments.append(PaymentModel(
                                    wallet_id = user.wallet.id,
                                    user_id =user.id,
                                    amount = payload.amount,
                                    payment_type =PaymentEnum.DEBIT,
                                    reference = trnxId,
                                    event = "charge.processing",
                                    status = "started",
                                    channel = ChannelEnum.WEB,
                                    statusCode = TransactionCodeEnum.PROCESSING,
                                    statusDescription = TransactionStatusEnum.PROCESSING,
                                    recipient=user.cashout_account,
                                    statusMessage = f"Cashout to {user.cashout_account} {user.cashout_bank}",
                                    balanceBefore = user.wallet.availableBalance,
                                    balanceAfter = newBalance,
                                    product_id=cashoutPd.product_id,
                                    product_type_id=cashoutPd.id,  # Assuming product_id is 1 for cashout
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
                            )
                            updatedUser = paymentQuery.create(db=db,model=user)
                            if updatedUser:
                                payment = paymentQuery.getPaymentByReference(db=db,reference=trnxId)
                                if payment:
                                    if int(user.cashout_limit) >= int(dailyCashout):
                                        logger.info(f"Start processing cashout records ............... @ {datetime.now()}")
                                        headers =  {'Authorization': f'Bearer {setting.paystack_token}','content-type': 'application/json'}
                                        params ={"source": payment.cashout.source,"amount": payment.cashout.amount,"reference":payment.reference,"recipient": payment.cashout.recipient,"reason": payment.cashout.reason }
                                        result = util.http(f"{setting.paystack_url}transfer",params=params,headers=headers)
                                        paystackResponse = result.json()
                                        if result.status_code == 200:
                                            if paystackResponse and paystackResponse["status"] is True:
                                                recipientData = paystackResponse.get("data", {})
                                                payment.statusCode = TransactionCodeEnum.SUCCESS
                                                payment.statusDescription = TransactionStatusEnum.SUCCESS
                                                payment.status = "success"
                                                payment.event = "charge.success"
                                                payment.cashout.withdrawalStatus = WithrawalStatusEnum.COMPLETED,
                                                payment.cashout.statusCode = TransactionCodeEnum.SUCCESS,
                                                payment.cashout.statusDescription = TransactionStatusEnum.SUCCESS,
                                        else:
                                            payment.statusCode = TransactionCodeEnum.FAILED
                                            payment.statusDescription = TransactionStatusEnum.FAILED
                                            payment.status = "failed"
                                            payment.event = "charge.failed"
                                            payment.cashout.withdrawalStatus = WithrawalStatusEnum.FAILED,
                                            payment.cashout.statusCode = TransactionCodeEnum.FAILED,
                                            payment.cashout.statusDescription = TransactionStatusEnum.FAILED,
                                    else:
                                        logger.info(f"cashout daily limit exceeded at {datetime.now()}")
                                        payment.statusCode = TransactionCodeEnum.PROCESSING
                                        payment.statusDescription = TransactionStatusEnum.PROCESSING
                                        #payment.cashout.statusCode = TransactionCodeEnum.PROCESSING,
                                        #payment.cashout.statusDescription = TransactionStatusEnum.PROCESSING,
                                        #payment.cashout.withdrawalStatus = WithrawalStatusEnum.WAITING,
                                    saved = paymentQuery.create(db=db,model=payment)
                                    background_task.add_task(notifyUser,db=db,title=f"Cashout Notification", message=payment.statusDescription,userId=user.id, setting=setting)
                                        #email_debit = util.templates.TemplateResponse("debit.html",{"request": request, "user": user,"payment":createCashoutRecord},)
                                        #background_task.add_task(util.mailer,str(email_debit.body, "utf-8"),setting=setting,subject="Cashout Notification",toAddress=user.email)
                                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":payment.reference})
                                else:
                                    logger.info(f"Cashout not enabled for {user.firstname} {user.lastname} for {user.email} @ {datetime.now()}")
                                    response.status_code = status.HTTP_400_BAD_REQUEST 
                                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Payment not found Error")
                            else:
                                logger.info(f"Unable to process cashout for {user.firstname} {user.lastname} for {user.email} @ {datetime.now()}")
                                response.status_code = status.HTTP_400_BAD_REQUEST 
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Unable to process cashout")
                        else:
                            logger.info(f"Insufficient balance for {user.email} to cashout @ {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
                    else:
                        logger.info(f"cash service is not configured @ {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Cashout Error")
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


# Admin Payments
def adminPayments(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel,startDate: str,endDate: str):
    try:
        logger.info(
            f"started querying payments from {startDate} to {endDate}"
        )
        if admin.role.tag in [AdminRoleEnum.ADMIN,AdminRoleEnum.AUDIT,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.SUPERADMIN,AdminRoleEnum.HEADOFFICE,AdminRoleEnum.SUPPORT]:
            return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getAllPaymentsHistories(db=db,startDate=startDate,endDate=endDate)
            )
        else:
            return PaymentsResponse(
                statusCode= str(status.HTTP_200_OK),
                statusDescription=SUCCESS,
                data=queries.getAllPaymentsHistories(db=db,adminId=admin.id,startDate=startDate,endDate=endDate)
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
