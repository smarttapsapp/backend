
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import queries,adminQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.role import *
from schemas.admin import *
from schemas.general_ledger import *
from schemas.service_rate import *
from schemas.commission import *
from schemas.route import RoutesResponse,AddRouteRequest
from schemas.ticket import TicketsResponse
from schemas.bus import BusesResponse,AddBusRequest
from schemas.park import ParksResponse
from schemas.payment import BillPaymentResponse,BuyTicketRequest,BuyTrainTicketRequest
from schemas.train import TrainsResponse
from schemas.notification import NotificationsResponse
from services import notificationservice
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)

async def creditViaPaystackTransaction(request: Request,response:Response,setting: Setting,db: Session,biller:ProductTypeModel,customer:CustomerModel,payload:BuyTicketRequest,background_task:BackgroundTasks,bus:BusModel,remark:str=None,merchant:AdminModel=None):
    try:
        logger.info(f"started gl debit transaction for biller {biller.id} at {datetime.now()}")
        headoffice = queries.getHeadofficeAccount(db=db)
        if headoffice:
            logger.info(f"headoffice is configured at {datetime.now()}")
            provider = queries.getAdminById(db=db,adminId=bus.admin_id)
            if provider:
                logger.info(f"{provider.lastname}  is configured configured at {datetime.now()}")
                providerDiscount = queries.getAdminDiscount(db=db,adminId=provider.id)
                if providerDiscount:
                    logger.info(f"provider discount configured {datetime.now()}")
                    provider_cost = int(payload.amount) - int(providerDiscount.provider_discount_rate) if providerDiscount.provider_discount_type == CommissionType.percentage else int(payload.amount) * (1 - providerDiscount.provider_discount_rate)
                    netIncome = int(payload.amount) - provider_cost
                    merchant = queries.getMerchantByCustomerId(db=db,customerId=customer.id)
                    if not merchant:
                        merchant = headoffice
                    merchantCommission = queries.getAdminCommission(db=db,adminId=merchant.id)
                    logger.info(f"started checking available merchant commission at {datetime.now()}")
                    commissionAmount = 0
                    if merchantCommission:
                        logger.info(f"merchant is configured at {datetime.now()}")
                        commissionAmount = netIncome - int(merchantCommission.commission_rate) if merchantCommission.commission_type == CommissionType.calculated else (netIncome *  merchantCommission.commission_rate)
                    trnxId = f"{str(biller.billerId[:2]).upper()}-{util.generateId()}"
                    customer.wallet.availableBalance = int(customer.wallet.availableBalance) - int(payload.amount)
                    customer.wallet.updated_at = datetime.now()
                    customer.wallet.payments.append(
                        PaymentModel(wallet_id = customer.wallet.id,user_id =customer.id, amount = int(payload.amount),
                                        payment_type =PaymentEnum.DEBIT,reference =trnxId,event = "charge.success",status = "success",
                                        channel = ChannelEnum.MOBILE,providerAmount = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,
                                    statusDescription = TransactionStatusEnum.SUCCESS,commissionAmount = commissionAmount,
                                    product_type_id = biller.id,product_id=biller.product_id,recipient=customer.wallet.walletAccount,
                                    statusMessage =remark,balanceBefore = customer.wallet.availableBalance,code=setting.gl_outflow,
                                    balanceAfter = customer.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                    updatedCustomerAccount = queries.create(db=db,model=customer)
                    if updatedCustomerAccount:
                        background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
                        provider.wallet.availableBalance = int(provider.wallet.availableBalance) + int(provider_cost)
                        provider.wallet.updated_at = datetime.now()
                        provider.wallet.payments.append(PaymentModel(wallet_id = provider.wallet.id,admin_id = provider.id, amount = int(provider_cost),
                                    payment_type =PaymentEnum.CREDIT,reference =f"PUR-{util.generateId()}",code=providerDiscount.gl_to_provider,
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=provider.wallet.walletAccount,statusMessage =remark,balanceBefore = provider.wallet.availableBalance,
                                    balanceAfter = provider.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()),)
                        saveUpdatedProvider = queries.create(db=db,model=provider)
                        if saveUpdatedProvider:
                            background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                            merchant.wallet.availableBalance = int(merchant.wallet.availableBalance) + int(commissionAmount)
                            merchant.wallet.updated_at = datetime.now()
                            merchant.wallet.payments.append(PaymentModel(wallet_id=merchant.wallet.id,admin_id=merchant.id,amount = int(commissionAmount),
                                    payment_type =PaymentEnum.CREDIT,reference =f"COM-{util.generateId()}",code=setting.gl_inflow,
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=merchant.wallet.walletAccount,statusMessage = remark,balanceBefore =merchant.wallet.availableBalance,
                                    balanceAfter =merchant.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                            saveUpdatedMerchant = queries.create(db=db,model=merchant)
                            if saveUpdatedMerchant:
                                background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                headoffice.wallet.availableBalance = int(headoffice.wallet.availableBalance) + int(netIncome)
                                headoffice.wallet.updated_at = datetime.now()
                                headoffice.wallet.payments.append(PaymentModel(wallet_id = headoffice.wallet.id,admin_id =headoffice.id,amount = int(netIncome),
                                    payment_type =PaymentEnum.CREDIT,reference =f"INC-{util.generateId()}",event = "charge.success",
                                    payment_date = datetime.now().date(),status = "success",channel = ChannelEnum.MOBILE,code=setting.gl_inflow,transactionreference=trnxId,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=headoffice.wallet.walletAccount,statusMessage = remark,balanceBefore = headoffice.wallet.availableBalance,
                                    balanceAfter =headoffice.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                                saveUpdatedHeadoffice = queries.create(db=db,model=headoffice)
                                if saveUpdatedHeadoffice:
                                    background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                    ticketId =  f"BUS-{util.generateId()}"
                                    logger.info(f"create ticket record for bus with balance after {customer.wallet.availableBalance} ticket reference is {ticketId}")
                                    ticket = TicketModel(
                                        bus_id = bus.id,
                                        admin_id=bus.admin_id,
                                        customer_id = customer.id,
                                        route_id = payload.routeId,
                                        schedule_id = payload.scheduleId,
                                        qr_code = f"{ticketId}|{bus.bus_number}|{TicketModeEnum.BUS.value}|{customer.wallet.walletAccount}",
                                        mode = TicketModeEnum.BUS,
                                        price = int(payload.amount),
                                        ticket_number = ticketId,
                                        booked_at =datetime.now(),
                                        expired_at =datetime.now()+timedelta(days=2),
                                        created_at =datetime.now(),
                                        updated_at = datetime.now()
                                    )
                                    createTicketRecord = adminQuery.create(db=db,model=ticket)
                                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":createTicketRecord.ticket_number})
                                else:
                                    logger.info(f"Unable to credit system wallet at {datetime.now()}")
                                    response.status_code = status.HTTP_400_BAD_REQUEST
                                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                            else:
                                logger.info(f"Unable to credit merchant commission wallet at {datetime.now()}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                        else:
                            logger.info(f"Unable to credit provider wallet at {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                    else:
                        logger.info(f"Unable to debit customer wallet at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=DEBITFAILED)
                else:
                    logger.info(f"Service discount not configure at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERR)
            else:
                logger.info(f"Service provider has not been configured at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
        else:
            logger.info(f"Please configure headoffice to start transactions at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)
    except Exception as ex:
        logger.info(f"Error {ex} occurred while processing your debit transaction at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)

async def debitTransaction(response:Response,setting: Setting,db: Session,biller:ProductTypeModel,customerAccount:AccountModel,amount:int,background_task:BackgroundTasks,remark:str=None,merchant:AdminModel=None):
    try:
        logger.info(f"started gl debit transaction for biller {biller.id} at {datetime.now()}")
        role = adminQuery.getRoleByTag(db=db,tag=AdminRoleEnum.HEADOFFICE)
        logger.info(f"headoffice role is configured at {datetime.now()}")
        if role:
            headoffice = adminQuery.getAdminByRole(db=db,id=role.id)
            if headoffice:
                logger.info(f"headoffice is configured at {datetime.now()}")
                if not merchant:
                    merchant = headoffice
                serviceProvider = adminQuery.getServiceProviderByProduct(db=db,productTypeId=biller.id)
                if serviceProvider:
                    logger.info(f"{serviceProvider.admin.lastname}  is configured configured at {datetime.now()}")
                    provider_cost = amount - int(serviceProvider.provider_discount_rate) if serviceProvider.provider_discount_type == CommissionType.percentage else amount * (1 - serviceProvider.provider_discount_rate)
                    netIncome = amount - provider_cost
                    merchantCommission = adminQuery.getServiceCommissionByProduct(db=db,productTypeId=biller.id,adminId=merchant.id) if merchant else None
                    logger.info(f"started checking available merchant at {datetime.now()}")
                    commissionAmount = 0
                    if merchantCommission:
                        logger.info(f"merchant is configured at {datetime.now()}")
                        commissionAmount = netIncome - int(merchantCommission.commission_rate) if merchantCommission.commission_type == CommissionType.calculated else (netIncome *  merchantCommission.commission_rate)
                    trnxId = f"{str(biller.billerId[:2]).upper()}-{util.generateId()}"
                    # debit customer
                    customerAccount.availableBalance = int(customerAccount.availableBalance) - int(amount)
                    customerAccount.updated_at = datetime.now()
                    logger.info(f"started saving debit for customer at {datetime.now()}")
                    customerAccount.payments.append(PaymentModel(wallet_id = customerAccount.id,user_id =customerAccount.user_id, amount = int(amount),
                                     payment_type =PaymentEnum.DEBIT,reference =trnxId,
                                     event = "charge.success",
                                     status = "success",channel =ChannelEnum.MOBILE,providerAmount = provider_cost,statusCode = TransactionCodeEnum.PROCESSING,
                                     statusDescription = TransactionStatusEnum.PROCESSING,commissionAmount = commissionAmount,
                                     product_type_id = biller.id,product_id=biller.product_id,recipient=customerAccount.walletAccount,
                                     statusMessage = remark,balanceBefore = customerAccount.availableBalance,
                                     balanceAfter = customerAccount.availableBalance,created_at =datetime.now(),updated_at = datetime.now())),
                    savedCustomerAccount = adminQuery.save(db=db,account=customerAccount)
                    if savedCustomerAccount:
                        background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
                        serviceProvider.admin.wallet.availableBalance = int(serviceProvider.admin.wallet.availableBalance) + int(provider_cost)
                        serviceProvider.admin.wallet.updated_at = datetime.now()
                        serviceProvider.admin.wallet.payments.append(PaymentModel(wallet_id = serviceProvider.admin.wallet.id,admin_id = serviceProvider.admin_id, amount = int(provider_cost),
                                     payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                                     transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                     statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                     recipient=serviceProvider.admin.wallet.walletAccount,statusMessage = remark,balanceBefore = serviceProvider.admin.wallet.availableBalance,
                                     balanceAfter = serviceProvider.admin.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()),)
                        savedServiceProvider = adminQuery.create(db=db,model=serviceProvider)
                        if savedServiceProvider:
                            background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                            merchant.wallet.availableBalance = int(merchant.wallet.availableBalance) + int(commissionAmount)
                            merchant.wallet.updated_at = datetime.now()
                            merchant.wallet.payments.append(PaymentModel(wallet_id=merchant.wallet.id,admin_id=merchant.id,amount = int(commissionAmount),
                                     payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                                     transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                     fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                     recipient=merchant.wallet.walletAccount,statusMessage = remark,balanceBefore =merchant.wallet.availableBalance,
                                     balanceAfter =merchant.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                            savedMerchant = adminQuery.create(db=db,model=merchant)
                            if savedMerchant:
                                background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                headoffice.wallet.availableBalance = int(headoffice.wallet.availableBalance) + int(netIncome)
                                headoffice.wallet.updated_at = datetime.now()
                                headoffice.wallet.payments.append(PaymentModel(wallet_id = headoffice.wallet.id,admin_id =headoffice.id,amount = int(netIncome),
                                     payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                                     event = "charge.success",payment_date = datetime.now().date(),status = "success",channel = ChannelEnum.MOBILE,
                                     fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                     recipient=headoffice.wallet.walletAccount,statusMessage = remark,balanceBefore = headoffice.wallet.availableBalance,
                                     balanceAfter =headoffice.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                                savedHeadoffice = adminQuery.create(db=db,model=headoffice)
                                if savedHeadoffice:
                                    background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                    return BillPaymentResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":trnxId})
                                logger.info(f"Unable to credit system wallet at {datetime.now()}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                            logger.info(f"Unable to credit merchant commission wallet at {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                        logger.info(f"Unable to credit provider wallet at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                    logger.info(f"Unable to debit customer at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=DEBITFAILED)
                logger.info(f"Service provider has not been configured at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
            logger.info(f"Please configure headoffice to start transactions at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)
        logger.info(f"headoffice role has not been configured at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERR)
    except Exception as ex:
        logger.info(f"Error {ex} occurred while processing your debit transaction at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BillPaymentResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)

async def debitBusTransaction(request: Request,response:Response,setting: Setting,db: Session,biller:ProductTypeModel,customer:CustomerModel,payload:BuyTicketRequest,route:BusRouteModel,background_task:BackgroundTasks,bus:BusModel,remark:str=None,merchant:AdminModel=None):
    try:
        logger.info(f"started gl debit transaction for biller {biller.id} customer {customer.email} {customer.wallet.availableBalance} at {datetime.now()}")
        headoffice = queries.getHeadofficeAccount(db=db)
        if headoffice:
            logger.info(f"headoffice is configured at {datetime.now()}")
            provider = queries.getAdminById(db=db,adminId=bus.admin_id)
            if provider:
                logger.info(f"{provider.lastname}  is configured configured at {datetime.now()}")
                providerDiscount = queries.getAdminDiscount(db=db,adminId=provider.id)
                if providerDiscount:
                    logger.info(f"provider discount configured {datetime.now()}")
                    provider_cost = int(payload.amount) - int(providerDiscount.provider_discount_rate) if providerDiscount.provider_discount_type == CommissionType.percentage else int(payload.amount) * (1 - providerDiscount.provider_discount_rate)
                    netIncome = int(payload.amount) - provider_cost
                    merchant = queries.getMerchantByCustomerId(db=db,customerId=customer.id)
                    if not merchant:
                        merchant = headoffice
                    merchantCommission = queries.getAdminCommission(db=db,adminId=merchant.id)
                    logger.info(f"started checking available merchant commission at {datetime.now()}")
                    commissionAmount = 0
                    if merchantCommission:
                        logger.info(f"merchant is configured at {datetime.now()}")
                        commissionAmount = netIncome - int(merchantCommission.commission_rate) if merchantCommission.commission_type == CommissionType.calculated else (netIncome *  merchantCommission.commission_rate)
                    trnxId = f"{str(biller.billerId[:2]).upper()}-{util.generateId()}"
                    customer.wallet.availableBalance = int(customer.wallet.availableBalance) - int(payload.amount)
                    customer.wallet.updated_at = datetime.now()
                    customer.wallet.payments.append(
                        PaymentModel(wallet_id = customer.wallet.id,user_id =customer.id, amount = int(payload.amount),
                                        payment_type =PaymentEnum.DEBIT,reference =trnxId,event = "charge.success",status = "success",
                                        channel = ChannelEnum.MOBILE,providerAmount = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,
                                    statusDescription = TransactionStatusEnum.SUCCESS,commissionAmount = commissionAmount,
                                    product_type_id = biller.id,product_id=biller.product_id,recipient=customer.wallet.walletAccount,
                                    statusMessage =remark,balanceBefore = customer.wallet.availableBalance,code=setting.gl_outflow,
                                    balanceAfter = customer.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                    updatedCustomerAccount = queries.create(db=db,model=customer)
                    if updatedCustomerAccount:
                        background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
                        provider.wallet.availableBalance = int(provider.wallet.availableBalance) + int(provider_cost)
                        provider.wallet.updated_at = datetime.now()
                        provider.wallet.payments.append(PaymentModel(wallet_id = provider.wallet.id,admin_id = provider.id, amount = int(provider_cost),
                                    payment_type =PaymentEnum.CREDIT,reference =f"PUR-{util.generateId()}",code=providerDiscount.gl_to_provider,
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=provider.wallet.walletAccount,statusMessage =remark,balanceBefore = provider.wallet.availableBalance,
                                    balanceAfter = provider.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()),)
                        saveUpdatedProvider = queries.create(db=db,model=provider)
                        if saveUpdatedProvider:
                            background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                            merchant.wallet.availableBalance = int(merchant.wallet.availableBalance) + int(commissionAmount)
                            merchant.wallet.updated_at = datetime.now()
                            merchant.wallet.payments.append(PaymentModel(wallet_id=merchant.wallet.id,admin_id=merchant.id,amount = int(commissionAmount),
                                    payment_type =PaymentEnum.CREDIT,reference =f"COM-{util.generateId()}",code=setting.gl_inflow,
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=merchant.wallet.walletAccount,statusMessage = remark,balanceBefore =merchant.wallet.availableBalance,
                                    balanceAfter =merchant.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                            saveUpdatedMerchant = queries.create(db=db,model=merchant)
                            if saveUpdatedMerchant:
                                background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                headoffice.wallet.availableBalance = int(headoffice.wallet.availableBalance) + int(netIncome)
                                headoffice.wallet.updated_at = datetime.now()
                                headoffice.wallet.payments.append(PaymentModel(wallet_id = headoffice.wallet.id,admin_id =headoffice.id,amount = int(netIncome),
                                    payment_type =PaymentEnum.CREDIT,reference =f"INC-{util.generateId()}",event = "charge.success",
                                    payment_date = datetime.now().date(),status = "success",channel = ChannelEnum.MOBILE,code=setting.gl_inflow,transactionreference=trnxId,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=headoffice.wallet.walletAccount,statusMessage = remark,balanceBefore = headoffice.wallet.availableBalance,
                                    balanceAfter =headoffice.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                                saveUpdatedHeadoffice = queries.create(db=db,model=headoffice)
                                if saveUpdatedHeadoffice:
                                    background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                    ticketId =  f"BUS-{util.generateId()}"
                                    logger.info(f"create ticket record for bus with balance after {customer.wallet.availableBalance} ticket reference is {ticketId}")
                                    ticket = TicketModel(
                                        bus_id = bus.id,
                                        admin_id=bus.admin_id,
                                        customer_id = customer.id,
                                        busroute_id = route.id,
                                        busschedule_id = payload.scheduleId,
                                        boarding_date = payload.boardingDate,
                                        qr_code = f"{ticketId}|{bus.bus_number}|{TicketModeEnum.BUS.value}|{customer.wallet.walletAccount}",
                                        mode = TicketModeEnum.BUS,
                                        price = int(payload.amount),
                                        ticket_number = ticketId,
                                        booked_at =datetime.now(),
                                        expired_at =datetime.now()+timedelta(days=2),
                                        created_at =datetime.now(),
                                        updated_at = datetime.now()
                                    )
                                    createTicketRecord = adminQuery.create(db=db,model=ticket)
                                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":createTicketRecord.ticket_number})
                                else:
                                    logger.info(f"Unable to credit system wallet at {datetime.now()}")
                                    response.status_code = status.HTTP_400_BAD_REQUEST
                                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                            else:
                                logger.info(f"Unable to credit merchant commission wallet at {datetime.now()}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                        else:
                            logger.info(f"Unable to credit provider wallet at {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PENDING)
                    else:
                        logger.info(f"Unable to debit customer wallet at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=DEBITFAILED)
                else:
                    logger.info(f"Service discount not configure at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERR)
            else:
                logger.info(f"Service provider has not been configured at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
        else:
            logger.info(f"Please configure headoffice to start transactions at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)
    except Exception as ex:
        logger.info(f"Error {ex} occurred while processing your debit transaction at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)

async def debitTrainTransaction(request: Request,response:Response,setting:Setting,db:Session,biller:ProductTypeModel,customer:CustomerModel,payload:BuyTrainTicketRequest,train:TrainModel,seat:SeatModel,schedule:ScheduleModel,route:RouteModel,background_task:BackgroundTasks):
    try:
        logger.info(f"started gl debit transaction for biller {biller.billerName} at {datetime.now()}")
        remark = f"{str(biller.billerId[:2]).upper()}/{train.trainNumber[:2]}/{seat.classType}"
        headoffice = queries.getHeadofficeAccount(db=db)
        if headoffice:
            logger.info(f"headoffice is configured at {datetime.now()}")
            provider = queries.getAdminById(db=db,adminId=train.admin_id)
            if provider:
                logger.info(f"{provider.lastname}  is the provider at {datetime.now()}")
                providerDiscount = queries.getAdminDiscount(db=db,adminId=provider.id)
                if providerDiscount:
                    logger.info(f"provider discount configured {datetime.now()}")
                    provider_cost = int(payload.amount) - int(providerDiscount.provider_discount_rate) if providerDiscount.provider_discount_type == CommissionType.percentage else int(payload.amount) * (1 - providerDiscount.provider_discount_rate)
                    netIncome = int(payload.amount) - provider_cost
                    merchant = queries.getMerchantByCustomerId(db=db,customerId=customer.id)
                    if not merchant:
                        merchant = headoffice
                    merchantCommission = queries.getAdminCommission(db=db,adminId=merchant.id)
                    logger.info(f"started checking available merchant commission at {datetime.now()}")
                    commissionAmount = 0
                    if merchantCommission:
                        logger.info(f"merchant is configured at {datetime.now()}")
                        commissionAmount = netIncome - int(merchantCommission.commission_rate) if merchantCommission.commission_type == CommissionType.calculated else (netIncome *  merchantCommission.commission_rate)
                    trnxId = f"{str(biller.billerId[:2]).upper()}-{util.generateId()}"
                    customer.wallet.availableBalance = int(customer.wallet.availableBalance) - int(payload.amount)
                    customer.wallet.updated_at = datetime.now()
                    customer.wallet.payments.append(
                        PaymentModel(wallet_id = customer.wallet.id,user_id =customer.id, amount = int(payload.amount),
                                        payment_type =PaymentEnum.DEBIT,reference =trnxId,event = "charge.success",status = "success",
                                        channel = ChannelEnum.MOBILE,providerAmount = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,
                                    statusDescription = TransactionStatusEnum.SUCCESS,commissionAmount = commissionAmount,
                                    product_type_id = biller.id,product_id=biller.product_id,recipient=customer.wallet.walletAccount,
                                    statusMessage =remark,balanceBefore = customer.wallet.availableBalance,code=setting.gl_outflow,
                                    balanceAfter = customer.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                    updatedCustomerAccount = queries.create(db=db,model=customer)
                    if updatedCustomerAccount:
                        background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
                        provider.wallet.availableBalance = int(provider.wallet.availableBalance) + int(provider_cost)
                        provider.wallet.updated_at = datetime.now()
                        provider.wallet.payments.append(PaymentModel(wallet_id = provider.wallet.id,admin_id = provider.id, amount = int(provider_cost),
                                    payment_type =PaymentEnum.CREDIT,reference =f"PUR-{util.generateId()}",code=providerDiscount.gl_to_provider,
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=provider.wallet.walletAccount,statusMessage =remark,balanceBefore = provider.wallet.availableBalance,
                                    balanceAfter = provider.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()),)
                        saveUpdatedProvider = queries.create(db=db,model=provider)
                        if saveUpdatedProvider:
                            background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                            merchant.wallet.availableBalance = int(merchant.wallet.availableBalance) + int(commissionAmount)
                            merchant.wallet.updated_at = datetime.now()
                            merchant.wallet.payments.append(PaymentModel(wallet_id=merchant.wallet.id,admin_id=merchant.id,amount = int(commissionAmount),
                                    payment_type =PaymentEnum.CREDIT,reference =f"COM-{util.generateId()}",code=setting.gl_inflow,
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=merchant.wallet.walletAccount,statusMessage = remark,balanceBefore =merchant.wallet.availableBalance,
                                    balanceAfter =merchant.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                            saveUpdatedMerchant = queries.create(db=db,model=merchant)
                            if saveUpdatedMerchant:
                                background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                headoffice.wallet.availableBalance = int(headoffice.wallet.availableBalance) + int(netIncome)
                                headoffice.wallet.updated_at = datetime.now()
                                headoffice.wallet.payments.append(PaymentModel(wallet_id = headoffice.wallet.id,admin_id =headoffice.id,amount = int(netIncome),
                                    payment_type =PaymentEnum.CREDIT,reference =f"INC-{util.generateId()}",event = "charge.success",
                                    payment_date = datetime.now().date(),status = "success",channel = ChannelEnum.MOBILE,code=setting.gl_inflow,transactionreference=trnxId,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=headoffice.wallet.walletAccount,statusMessage = remark,balanceBefore = headoffice.wallet.availableBalance,
                                    balanceAfter =headoffice.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                                saveUpdatedHeadoffice = queries.create(db=db,model=headoffice)
                                if saveUpdatedHeadoffice:
                                    background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                    ticketId =  f"TRN-{util.generateId()}"
                                    logger.info(f"create ticket record for bus with balance after {customer.wallet.availableBalance} ticket reference is {ticketId}")
                                    ticket = TicketModel(
                                        train_id = train.id,
                                        admin_id=train.admin_id,
                                        customer_id = customer.id,
                                        route_id = route.id,
                                        schedule_id = schedule.id,
                                        boarding_date = payload.tripDate,
                                        seat_id =seat.id,
                                        qr_code = f"{ticketId}|{train.trainNumber}|{TicketModeEnum.TRAIN.value}|{customer.wallet.walletAccount}",
                                        mode = TicketModeEnum.TRAIN,
                                        price = int(payload.amount),
                                        ticket_number = ticketId,
                                        booked_at =datetime.now(),
                                        expired_at =datetime.now()+timedelta(days=2),
                                        created_at =datetime.now(),
                                        updated_at = datetime.now()
                                    )
                                    createTicketRecord = adminQuery.create(db=db,model=ticket)
                                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"transactionId":createTicketRecord.ticket_number})
                                else:
                                    logger.info(f"Unable to credit system wallet at {datetime.now()}")
                                    response.status_code = status.HTTP_400_BAD_REQUEST
                                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                            else:
                                logger.info(f"Unable to credit merchant commission wallet at {datetime.now()}")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                        else:
                            logger.info(f"Unable to credit provider wallet at {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                    else:
                        logger.info(f"Unable to debit customer at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=DEBITFAILED)
                else:
                    logger.info(f"Service provider has not been configured at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
            else:
                logger.info(f"Please configure service provider to start transactions at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)
        else:
            logger.info(f"headoffice role has not been configured at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERR)
    except Exception as ex:
        logger.info(f"Error {ex} occurred while processing your debit transaction at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)

async def redeemTicket(response:Response,setting: Setting,db: Session,biller:ProductTypeModel,ticket:TicketModel,background_task:BackgroundTasks,remark:str="Redeem Ticket",merchant:AdminModel=None):
    try:
        logger.info(f"started gl debit transaction for biller {biller.id} at {datetime.now()}")
        role = adminQuery.getRoleByTag(db=db,tag=AdminRoleEnum.HEADOFFICE)
        logger.info(f"headoffice role is configured at {datetime.now()}")
        if role:
            headoffice = adminQuery.getAdminByRole(db=db,id=role.id)
            if headoffice:
                logger.info(f"headoffice is configured at {datetime.now()}")
                if not merchant:
                    merchant = headoffice
                serviceProvider = adminQuery.getServiceProviderByProduct(db=db,productTypeId=biller.id)
                if serviceProvider:
                    logger.info(f"{serviceProvider.admin.lastname}  is configured configured at {datetime.now()}")
                    provider_cost = int(ticket.price) - int(serviceProvider.provider_discount_rate) if serviceProvider.provider_discount_type == CommissionType.percentage else int(ticket.price) * (1 - serviceProvider.provider_discount_rate)
                    netIncome = int(ticket.price) - provider_cost
                    merchantCommission = adminQuery.getServiceCommissionByProduct(db=db,productTypeId=biller.id,adminId=merchant.id) if merchant else None
                    logger.info(f"started checking available merchant at {datetime.now()}")
                    commissionAmount = 0
                    if merchantCommission:
                        logger.info(f"merchant is configured at {datetime.now()}")
                        commissionAmount = netIncome - int(merchantCommission.commission_rate) if merchantCommission.commission_type == CommissionType.calculated else (netIncome *  merchantCommission.commission_rate)
                    trnxId = f"{str(biller.billerId[:2]).upper()}-{util.generateId()}"
                    background_task.add_task(notificationservice.sendNotification,notificationType="debit",setting=setting,background_task=background_task)
                    serviceProvider.admin.wallet.availableBalance = int(serviceProvider.admin.wallet.availableBalance) + int(provider_cost)
                    serviceProvider.admin.wallet.updated_at = datetime.now()
                    serviceProvider.admin.wallet.payments.append(PaymentModel(wallet_id = serviceProvider.admin.wallet.id,admin_id = serviceProvider.admin_id, amount = int(provider_cost),
                                    payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=serviceProvider.admin.wallet.walletAccount,statusMessage = remark,balanceBefore = serviceProvider.admin.wallet.availableBalance,
                                    balanceAfter = serviceProvider.admin.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()),)
                    savedServiceProvider = adminQuery.create(db=db,model=serviceProvider)
                    if savedServiceProvider:
                        background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                        merchant.wallet.availableBalance = int(merchant.wallet.availableBalance) + int(commissionAmount)
                        merchant.wallet.updated_at = datetime.now()
                        merchant.wallet.payments.append(PaymentModel(wallet_id=merchant.wallet.id,admin_id=merchant.id,amount = int(commissionAmount),
                                    payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                                    transactionreference=trnxId,event = "charge.success",status = "success",channel =ChannelEnum.MOBILE,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=merchant.wallet.walletAccount,statusMessage = remark,balanceBefore =merchant.wallet.availableBalance,
                                    balanceAfter =merchant.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                        savedMerchant = adminQuery.create(db=db,model=merchant)
                        if savedMerchant:
                            background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                            headoffice.wallet.availableBalance = int(headoffice.wallet.availableBalance) + int(netIncome)
                            headoffice.wallet.updated_at = datetime.now()
                            headoffice.wallet.payments.append(PaymentModel(wallet_id = headoffice.wallet.id,admin_id =headoffice.id,amount = int(netIncome),
                                    payment_type =PaymentEnum.CREDIT,reference =f"{str(biller.billerId[:2]).upper()}-{util.generateId()}",
                                    event = "charge.success",payment_date = datetime.now().date(),status = "success",channel = ChannelEnum.MOBILE,
                                    fee = provider_cost,statusCode = TransactionCodeEnum.SUCCESS,statusDescription = TransactionStatusEnum.SUCCESS,product_type_id = biller.id,product_id=biller.product_id,
                                    recipient=headoffice.wallet.walletAccount,statusMessage = remark,balanceBefore = headoffice.wallet.availableBalance,
                                    balanceAfter =headoffice.wallet.availableBalance,created_at =datetime.now(),updated_at = datetime.now()))
                            savedHeadoffice = adminQuery.create(db=db,model=headoffice)
                            if savedHeadoffice:
                                ticket.status = TicketStatusEnum.USED
                                ticket.updated_at = datetime.now()
                                queries.create(db=db,model=ticket)
                                background_task.add_task(notificationservice.sendNotification,notificationType="credit",setting=setting,background_task=background_task)
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                            logger.info(f"Unable to credit system wallet at {datetime.now()}")
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                        logger.info(f"Unable to credit merchant commission wallet at {datetime.now()}")
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                    logger.info(f"Unable to credit provider wallet at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
                logger.info(f"Service provider has not been configured at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
            logger.info(f"Please configure headoffice to start transactions at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERROR)
        logger.info(f"headoffice role has not been configured at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SERVICEERR)
    except Exception as ex:
        logger.info(f"Error {ex} occurred while processing your debit transaction at {datetime.now()}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
# ledger
async def listOfLedgers(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying ledger..............@ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            return GLedgersResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getGlAccounts(db=db))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return GLedgersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return GLedgersResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addLedger(db: Session,setting: Setting,payload: AddGLRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new ledger @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            if payload.id:
                logger.info(f"started updating ledger {payload.id} @ {datetime.now()}")
                existing = adminQuery.getGlAccountById(db=db,id=payload.id)
                if existing:
                    existing.name = payload.name
                    existing.gl_type = payload.gl_type
                    existing.updated_at = datetime.now()
                    created = queries.create(db=db,model=existing)
                    if created:
                        email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                        background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Ledger",toAddress=admin.email,)
                        return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
            else:
                glcode = f"GL{util.generateId()}"
                new = GLAccountModel(name=payload.name,code=glcode,gl_type=AccountType(payload.gl_type),created_at=datetime.now(),updated_at=datetime.now(),)
                created = queries.create(db=db,model=new)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Ledger",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteLedger(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,id: int):
    try:
        logger.info(f"started deleting GlAccount {id} @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            existing = adminQuery.deleteGlAccount(db=db,id=id)
            if existing:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# ledger
async def listOfCommissions(request: Request,response: Response,setting: Setting,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying ledger..............@ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            return CommissionsResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getServiceCommissions(db=db))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addCommission(db: Session,setting: Setting,payload: AddCommissionRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new ledger @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            if payload.id:
                logger.info(f"started updating ledger {payload.id} @ {datetime.now()}")
                existing = adminQuery.getServiceCommissionById(db=db,id=payload.id)
                if existing:
                    existing.commission_rate = payload.commission_rate
                    existing.commission_type = payload.commission_type
                    existing.updated_at = datetime.now()
                    created = adminQuery.create(db=db,model=existing)
                    if created:
                        email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                        background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="Update on Service Commission",toAddress=admin.email,)
                        return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
            else:
                new = CommissionModel(product_type_id=payload.product_type_id,admin_id=payload.admin_id,commission_type=payload.commission_type,commission_rate=payload.commission_rate,created_at=datetime.now(),updated_at=datetime.now(),)
                created = adminQuery.create(db=db,model=new)
                if created:
                    email_body = util.templates.TemplateResponse("onboarding.html",{"request": request, "user": admin,},)
                    background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject="New Service commission",toAddress=admin.email,)
                    return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteCommission(db: Session, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel,id: int):
    try:
        logger.info(f"started deleting Commission {id} @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            existing = adminQuery.deleteServiceCommission(db=db,id=id)
            if existing:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
# ledger
async def listOfDiscounts(response: Response,db: Session,admin: AdminModel):
    try:
        logger.info(f"started querying ledger..............@ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT,AdminRoleEnum.BUSINESS]:
            return ProvidersResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=adminQuery.getServiceProviders(db=db))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def addDiscount(db: Session,setting: Setting,payload: AddProviderRateRequest, background_task: BackgroundTasks, request: Request,response: Response,admin:AdminModel):
    try:
        logger.info(f"started creating new ledger at {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:            
            existing = adminQuery.getServiceProviderById(db=db,id=payload.id)
            if existing:
                subject = "Update on Service Provider Discount"
                logger.info(f"started updating ledger {payload.id} at {datetime.now()}")
                existing.provider_discount_rate = payload.provider_discount_rate
                existing.provider_discount_type = payload.provider_discount_type
                existing.active = payload.active
                existing.updated_at = datetime.now()
                created = adminQuery.disableServiceProviderByProduct(db=db,productId=existing.product_type_id,active=not payload.active,model=existing)
            else:
                subject = "New Service Provider Discount"
                logger.info(f"started creating new service provider discount @ {datetime.now()}")
                existing = ServiceRateModel(admin_id=payload.admin_id,product_type_id=payload.product_type_id,provider_discount_type=payload.provider_discount_type,provider_discount_rate=payload.provider_discount_rate,active=payload.active,gl_to_provider=payload.gl_to_provider,created_at=datetime.now(),updated_at=datetime.now(),)
                newlycreated = queries.create(db=db,model=existing)
                created = adminQuery.disableServiceProviderByProduct(db=db,productId=existing.product_type_id,active=not payload.active,model=newlycreated)
            if created:
                email_body = util.templates.TemplateResponse("service_discount.html",{"request": request, "user": admin,},)
                background_task.add_task(util.mailer,str(email_body.body, "utf-8"),setting=setting,subject=subject,toAddress=admin.email,)
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(statusCode = str(status.HTTP_401_UNAUTHORIZED),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
async def deleteDiscount(db: Session,response: Response, background_task: BackgroundTasks, request: Request,admin:AdminModel,id: int):
    try:
        logger.info(f"started deleting Discount {id} @ {datetime.now()}")
        if admin.role.tag in [AdminRoleEnum.SUPERADMIN,AdminRoleEnum.ACCOUNTANT]:
            existing = adminQuery.deleteServiceDiscount(db=db,discountId=id)
            if existing:
                response.status_code = status.HTTP_200_OK
                return BaseResponse(statusCode = str(status.HTTP_200_OK),statusDescription=SUCCESS)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=NOTEXIST)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode = str(status.HTTP_400_BAD_REQUEST),statusDescription=UNAUTHORISED)
    except Exception as ex:
        logger.error(str(ex))
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY)    
