
import logging

from task.celery_app import celery_app
from datetime import datetime, timedelta
from utils.database import CelerySessionLocal
from sqlalchemy import desc,asc
from utils import util
from services import glAccountingService
from models.model import TransactionModel,AdminModel,ProductModel,ProductTypeModel,PackageModel
from utils.dependencies import getSystemSetting
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def requery_pending_transactions(self):
    db = CelerySessionLocal()
    cutoff = datetime.now() - timedelta(minutes=10)
    try:
        setting= getSystemSetting(db=db)
        txns = (db.query(TransactionModel).filter(TransactionModel.statusCode == "C001",TransactionModel.created_at <= cutoff).order_by(asc(TransactionModel.created_at)).with_for_update().limit(5).all() )
        for txn in txns:
            if txn.reference:
                logger.info(f"Requerying transaction with reference {txn.reference} and status {txn.statusCode} for the time at {str(datetime.now())}")
                response = transactionRequery(db=db,transaction=txn,setting=setting)
                if response.statusCode == "200":
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
                else:
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
            else:
                txn.statusCode = "C13"
                txn.statusMessage = "Transaction has no reference for requery"
                logger.info(f"Transaction with id {txn.id} phone {txn.recipient} done at {txn.created_at} has no reference for requery at {str(datetime.now())}")
            txn.updated_at = datetime.now()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
@celery_app.task(bind=True)
def run_product_updates(self):
    db = CelerySessionLocal()
    try:
        provider = (db.query(AdminModel).filter(AdminModel.identifier == "topupbox").first())
        if provider:
            logger.info(f"Started product update for provider {provider.identifier} at {str(datetime.now())}")
            products = db.query(ProductModel).all()
            if products:
                logger.info(f"Found {len(products)} products to update for provider {provider.identifier} at {str(datetime.now())}")
                for product in products:
                    if product.vasType=="data":
                        headers = {"Content-Type": "application/json","Authorization": provider.provider_auth}
                        res = util.http(url=f'{provider.provider_url}data-providers',headers=headers)
                        if res.status_code == 200:
                            logger.info(f"Successfully fetched providers for {product.vasType} from provider {provider.identifier} at {str(datetime.now())}")
                            jsonResponse = res.json()
                            if jsonResponse['status'] == "2000":
                                for productType in jsonResponse["data"]:
                                    existingProductType = db.query(ProductTypeModel).filter(ProductTypeModel.billerId == productType["serviceType"]).first()
                                    if existingProductType:
                                        existingProductType.billerName = productType["shortname"]
                                        existingProductType.hasPackages = True
                                        existingProductType.updated_at = datetime.now()
                                        db.commit()
                                        res2 = util.http(url=f'{provider.provider_url}internet-bundle',params={"serviceType": productType["serviceType"]},headers=headers)
                                        if res2.status_code == 200:
                                            jsonResponse2 = res2.json()
                                            if jsonResponse2['status'] == "2000":
                                                for packages in jsonResponse2["data"]:
                                                    existingPackage = db.query(PackageModel).filter(PackageModel.packageCode == packages["datacode"]).first()
                                                    if existingPackage:
                                                        existingPackage.description = packages["name"]
                                                        existingPackage.amount = str(int(packages["price"])*100)
                                                        existingPackage.packageCode = packages["datacode"]
                                                        existingPackage.updated_at = datetime.now()
                                                    else:
                                                        newPackage = PackageModel(billerId=productType["serviceType"],product_type_id=existingProductType.id,packageCode=packages["datacode"],description=packages["name"],status=True,amount=str(int(packages["price"])*100),created_at=datetime.now())
                                                        db.add(newPackage)
                                                        db.commit()
                                            else:
                                                logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                        else:
                                            logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                    else:
                                        newProductType = ProductTypeModel(billerId=productType["serviceType"],billerName=productType["shortname"],hasLookup=False,hasPackages=True,billerType="data",created_at = datetime.now(),product_id = product.id,service_provider_id = provider.id)
                                        db.add(newProductType)
                                        db.commit()
                                        db.refresh(newProductType)
                                        res2 = util.http(url=f'{provider.provider_url}internet-bundle',params={"serviceType": productType["serviceType"]},headers=headers)
                                        if res2.status_code == 200:
                                            jsonResponse2 = res2.json()
                                            if jsonResponse2['status'] == "2000":
                                                for packages in jsonResponse2["data"]:
                                                    newPackage = PackageModel(billerId=productType["serviceType"],product_type_id=existingProductType.id,packageCode=packages["datacode"],description=packages["name"],status=True,amount=str(int(packages["price"])*100),created_at=datetime.now())
                                                    db.add(newPackage)
                                                    db.commit()
                                            else:
                                                logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                        else:
                                            logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                            else:
                                logger.info(f"Failed to fetch providers for {product.vasType} from provider {provider.identifier} at {str(datetime.now())}")
                    elif product.vasType=="cabletv":
                        headers = {"Content-Type": "application/json","Authorization": provider.provider_auth}
                        res = util.http(url=f'{provider.provider_url}cable-providers',headers=headers)
                        if res.status_code == 200:
                            logger.info(f"Successfully fetched providers for {product.vasType} from provider {provider.identifier} at {str(datetime.now())}")
                            jsonResponse = res.json()
                            if jsonResponse['status'] == "2000":
                                for productType in jsonResponse["data"]:
                                    existingProductType = db.query(ProductTypeModel).filter(ProductTypeModel.billerId == productType["serviceType"]).first()
                                    if existingProductType:
                                        existingProductType.billerName = productType["shortname"]
                                        existingProductType.hasPackages = True
                                        existingProductType.updated_at = datetime.now()
                                        db.commit()
                                        res2 = util.http(url=f'{provider.provider_url}internet-bundle',params={"serviceType": productType["serviceType"]},headers=headers)
                                        if res2.status_code == 200:
                                            jsonResponse2 = res2.json()
                                            if jsonResponse2['status'] == "2000":
                                                for packages in jsonResponse2["data"]:
                                                    existingPackage = db.query(PackageModel).filter(PackageModel.packageCode == packages["datacode"]).first()
                                                    if existingPackage:
                                                        existingPackage.description = packages["name"]
                                                        existingPackage.amount = str(int(packages["price"])*100)
                                                        existingPackage.packageCode = packages["datacode"]
                                                        existingPackage.updated_at = datetime.now()
                                                    else:
                                                        newPackage = PackageModel(billerId=productType["serviceType"],product_type_id=existingProductType.id,packageCode=packages["datacode"],description=packages["name"],status=True,amount=str(int(packages["price"])*100),created_at=datetime.now())
                                                        db.add(newPackage)
                                                        db.commit()
                                            else:
                                                logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                        else:
                                            logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                    else:
                                        newProductType = ProductTypeModel(billerId=productType["serviceType"],billerName=productType["shortname"],hasLookup=False,hasPackages=True,billerType="data",created_at = datetime.now(),product_id = product.id,service_provider_id = provider.id)
                                        db.add(newProductType)
                                        db.commit()
                                        db.refresh(newProductType)
                                        res2 = util.http(url=f'{provider.provider_url}internet-bundle',params={"serviceType": productType["serviceType"]},headers=headers)
                                        if res2.status_code == 200:
                                            jsonResponse2 = res2.json()
                                            if jsonResponse2['status'] == "2000":
                                                for packages in jsonResponse2["data"]:
                                                    newPackage = PackageModel(billerId=productType["serviceType"],product_type_id=existingProductType.id,packageCode=packages["datacode"],description=packages["name"],status=True,amount=str(int(packages["price"])*100),created_at=datetime.now())
                                                    db.add(newPackage)
                                                    db.commit()
                                            else:
                                                logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                        else:
                                            logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                            else:
                                logger.info(f"Failed to fetch providers for {product.vasType} from provider {provider.identifier} at {str(datetime.now())}")
                    elif product.vasType=="electricity":
                        headers = {"Content-Type": "application/json","Authorization": provider.provider_auth}
                        res = util.http(url=f'{provider.provider_url}data-providers',headers=headers)
                        if res.status_code == 200:
                            logger.info(f"Successfully fetched providers for {product.vasType} from provider {provider.identifier} at {str(datetime.now())}")
                            jsonResponse = res.json()
                            if jsonResponse['status'] == "2000":
                                for productType in jsonResponse["data"]:
                                    existingProductType = db.query(ProductTypeModel).filter(ProductTypeModel.billerId == productType["serviceType"]).first()
                                    if existingProductType:
                                        existingProductType.billerName = productType["shortname"]
                                        existingProductType.hasPackages = True
                                        existingProductType.updated_at = datetime.now()
                                        db.commit()
                                        res2 = util.http(url=f'{provider.provider_url}internet-bundle',params={"serviceType": productType["serviceType"]},headers=headers)
                                        if res2.status_code == 200:
                                            jsonResponse2 = res2.json()
                                            if jsonResponse2['status'] == "2000":
                                                for packages in jsonResponse2["data"]:
                                                    existingPackage = db.query(PackageModel).filter(PackageModel.packageCode == packages["datacode"]).first()
                                                    if existingPackage:
                                                        existingPackage.description = packages["name"]
                                                        existingPackage.amount = str(int(packages["price"])*100)
                                                        existingPackage.packageCode = packages["datacode"]
                                                        existingPackage.updated_at = datetime.now()
                                                    else:
                                                        newPackage = PackageModel(billerId=productType["serviceType"],product_type_id=existingProductType.id,packageCode=packages["datacode"],description=packages["name"],status=True,amount=str(int(packages["price"])*100),created_at=datetime.now())
                                                        db.add(newPackage)
                                                        db.commit()
                                            else:
                                                logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                        else:
                                            logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                    else:
                                        newProductType = ProductTypeModel(billerId=productType["serviceType"],billerName=productType["shortname"],hasLookup=False,hasPackages=True,billerType="data",created_at = datetime.now(),product_id = product.id,service_provider_id = provider.id)
                                        db.add(newProductType)
                                        db.commit()
                                        db.refresh(newProductType)
                                        res2 = util.http(url=f'{provider.provider_url}internet-bundle',params={"serviceType": productType["serviceType"]},headers=headers)
                                        if res2.status_code == 200:
                                            jsonResponse2 = res2.json()
                                            if jsonResponse2['status'] == "2000":
                                                for packages in jsonResponse2["data"]:
                                                    newPackage = PackageModel(billerId=productType["serviceType"],product_type_id=existingProductType.id,packageCode=packages["datacode"],description=packages["name"],status=True,amount=str(int(packages["price"])*100),created_at=datetime.now())
                                                    db.add(newPackage)
                                                    db.commit()
                                            else:
                                                logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                                        else:
                                            logger.info(f"Failed to fetch packages for {productType['shortname']} from provider {provider.identifier} at {str(datetime.now())}")
                            else:
                                logger.info(f"Failed to fetch providers for {product.vasType} from provider {provider.identifier} at {str(datetime.now())}")
            else:
                logger.info(f"No products found for provider {provider.provider_name} at {str(datetime.now())}")
        else:
            logger.info(f"No provider found with code INSURTECHIT for product update at {str(datetime.now())}")       
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
@celery_app.task(bind=True)
def emailNotification(self,subject:str,service:str,userId:int=None,adminId:int=None):
    print(message)
@celery_app.task(bind=True)
def run_auto_fund_wallet(self):
    db = CelerySessionLocal()
    cutoff = datetime.now() - timedelta(minutes=10)
    try:
        setting= getSystemSetting(db=db)
        txns = (db.query(TransactionModel).filter(TransactionModel.statusCode == "C001",TransactionModel.created_at <= cutoff).order_by(asc(TransactionModel.created_at)).with_for_update().limit(5).all() )
        for txn in txns:
            if txn.reference:
                logger.info(f"Requerying transaction with reference {txn.reference} and status {txn.statusCode} for the time at {str(datetime.now())}")
                response = transactionRequery(db=db,transaction=txn,setting=setting)
                if response.statusCode == "200":
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
                else:
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
            else:
                txn.statusCode = "C13"
                txn.statusMessage = "Transaction has no reference for requery"
                logger.info(f"Transaction with id {txn.id} phone {txn.recipient} done at {txn.created_at} has no reference for requery at {str(datetime.now())}")
            txn.updated_at = datetime.now()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
@celery_app.task(bind=True)
def paystackNotification(self):
    db = CelerySessionLocal()
    cutoff = datetime.now() - timedelta(minutes=10)
    try:
        setting= getSystemSetting(db=db)
        txns = (db.query(TransactionModel).filter(TransactionModel.statusCode == "C001",TransactionModel.created_at <= cutoff).order_by(asc(TransactionModel.created_at)).with_for_update().limit(5).all() )
        for txn in txns:
            if txn.reference:
                logger.info(f"Requerying transaction with reference {txn.reference} and status {txn.statusCode} for the time at {str(datetime.now())}")
                response = transactionRequery(db=db,transaction=txn,setting=setting)
                if response.statusCode == "200":
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
                else:
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
            else:
                txn.statusCode = "C13"
                txn.statusMessage = "Transaction has no reference for requery"
                logger.info(f"Transaction with id {txn.id} phone {txn.recipient} done at {txn.created_at} has no reference for requery at {str(datetime.now())}")
            txn.updated_at = datetime.now()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
@celery_app.task(bind=True,)
def process_gl_transactions(self,reference: str):
    try:
        setting = get_settings()
        asyncio.run(process_trigger(msisdn=msisdn,autotopupReference=autotopupReference,network=network,setting=setting,product=product))
    except Exception as exc:
        logger.exception(f"requery_pending_transactions unrecoverable {exc}")
@celery_app.task(bind=True,)
def process_app_notifications(self,customer: str):
    try:
        setting = get_settings()
        asyncio.run(process_trigger(msisdn=msisdn,autotopupReference=autotopupReference,network=network,setting=setting,product=product))
    except Exception as exc:
        logger.exception(f"requery_pending_transactions unrecoverable {exc}")
@celery_app.task(bind=True,)
def process_bills_payment(self,customer: str):
    try:
        setting = get_settings()
        asyncio.run(process_trigger(msisdn=msisdn,autotopupReference=autotopupReference,network=network,setting=setting,product=product))
    except Exception as exc:
        logger.exception(f"requery_pending_transactions unrecoverable {exc}")
@celery_app.task(bind=True,)
def process_bus_payment(self,transactionReference: str):
    try:
        setting = get_settings()
        db = CelerySessionLocal()
        asyncio.run(glAccountingService.process_cashout_payment(transactionReference=transactionReference,db=db,setting=setting))
    except Exception as exc:
        logger.exception(f"process_bus_payment unrecoverable {exc}")
    finally:
        db.close()
@celery_app.task(bind=True,)
def process_cashout_payment(self,transactionReference: str):
    try:
        setting = get_settings()
        db = CelerySessionLocal()
        asyncio.run(glAccountingService.process_cashout_payment(transactionReference=transactionReference,db=db,setting=setting))
    except Exception as exc:
        logger.exception(f"process_cashout_payment unrecoverable {exc}")
    finally:
        db.close()
    