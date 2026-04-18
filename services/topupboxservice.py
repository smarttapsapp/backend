

import logging
from utils import util
from models.model import *
from datetime import datetime
from schemas.setting import Setting
logger = logging.getLogger(__name__)

async def purchaseService(biller:ProductTypeModel, serviceprovider:AdminModel,params: dict = None):
    response = {}
    try:
        logger.info(f"started sending request to {serviceprovider.companyName} at {datetime.now()}")
        if str(biller.billerType).lower() == 'airtime':
            providerUrl = f"{serviceprovider.provider_url}recharge/{biller.billerId}/airtime"
        elif str(biller.billerType).lower() == 'data':
            providerUrl = f"{serviceprovider.provider_url}recharge/{biller.billerId}/data"
        elif biller.billerType == 'electricity':
            providerUrl = f"{serviceprovider.provider_url}services/bills/electricity-request"
        elif biller.billerType == 'cabletv':
            providerUrl = f"{serviceprovider.provider_url}services/bills/cable-request"
        header = {"Content-Type": "application/json","Authorization": serviceprovider.provider_auth}
        res = util.http(url=providerUrl,params=params,headers=header)
        jsonresponse = res.json()
        if res.status_code in[200,201]:
            if jsonresponse["status"] == "2000":
                response["statuscode"] = "200"
                response["tranxReference"] = jsonresponse["referenceNumber"]
                response["confirmCode"] = jsonresponse["confirmationCode"]
                response["mReference"] = jsonresponse["correlationId"]
                response["statusDescription"] = jsonresponse["message"]
                response["amount"] = jsonresponse["amount"]
            elif jsonresponse["status"] == "5010":
                response["statuscode"] = "C001"
                response["tranxReference"] = jsonresponse["referenceNumber"]
                response["statusDescription"] = jsonresponse["message"]
            else:
                response["statuscode"] = "C13"
                response["tranxReference"] = jsonresponse["referenceNumber"]
                response["statusDescription"] = jsonresponse["message"]
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def dataplans(biller:ProductTypeModel, serviceprovider:AdminModel):
    response = {}
    try:
        logger.info(
            f"started data plan request for {biller.billerName} {serviceprovider.lastname} at {datetime.now()}"
        )
        headers = {"Content-Type": "application/json","Authorization": serviceprovider.provider_auth}
        res = util.http(url=f'{serviceprovider.provider_url}/data-price-point/{biller.billerId}',headers=headers)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['status'] == "2000":
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse["data"]
            else:
                response["statuscode"] = "400"
                response["message"] = "failed"
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def billEnquriesService(serviceprovider:AdminModel,customerId: str,billerId: str):
    response = {}
    try:
        logger.info(
            f"started sending request to {serviceprovider.companyName} at {datetime.now()}"
        )
        headers = {"Content-Type": "application/json","Authorization": serviceprovider.provider_auth}
        res = util.http(url=f'{serviceprovider.provider_url}services/bills/verify-name-elec',params={"account_number":customerId,"service_type": billerId},headers=headers)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['status'] == "2000":
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse['data'][0] if jsonresponse['data'] else {}
            else:
                response["statuscode"] = "400"
                response["message"] = "failed"
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def requeryTopupBoxTransaction(payload):
    response = {}
    try:
        respd = openRequest(
            url=topupbox_url + "/services/api/v2/w1/query/" + payload[2],
            headers={
                "Authorization": topboxAuth,
                "Content-Type": "application/json",
            },
            timeouts=5,
        )
        if respd["status"] == "2000" or respd["status"] == 200:
            response["statusCode"] = "00"
            response["tranxReference"] = respd["refrenceNumber"]
            response["operatorCode"] = "05"
            response["amount"] = respd["amount"]
            response["mReference"] = payload[2]
            response["confirmCode"] = respd["confirmationCode"]
            response["statusDescription"] = respd["message"]
        else:
            response["statusCode"] = respd["status"]
            response["statusDescription"] = respd["message"]
            # response["data"] = respd
    except Exception as ex:
        print(ex)
        response["statusCode"] = "C001"
        response["statusDescription"] = "Pending"
    return response
async def cabletvProviders(product:ProductModel, serviceprovider:AdminModel):
    response = {}
    try:
        logger.info(
            f"started getting providerd for {product.name} {serviceprovider.lastname} at {datetime.now()}"
        )
        headers = {"Content-Type": "application/json","Authorization": serviceprovider.provider_auth}
        res = util.http(url=f'{serviceprovider.provider_url}services/bills/cabletv-providers',headers=headers)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['status'] == "2000":
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse["data"]
            else:
                response["statuscode"] = "400"
                response["message"] = "failed"
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def cabletvPackages(biller:ProductTypeModel):
    response = {}
    try:
        logger.info(
            f"started data plan request for {biller.billerName} {biller.provider.lastname} at {datetime.now()}"
        )
        headers = {"Content-Type": "application/json","Authorization": biller.provider.provider_auth}
        res = util.http(url=f'{biller.provider.provider_url}services/bills/multichoice-list',params={"service_type": biller.billerId},headers=headers)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['status'] == "2000":
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse["data"]
            else:
                response["statuscode"] = "400"
                response["message"] = "failed"
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def electricityProviders(product:ProductModel, serviceprovider:AdminModel):
    response = {}
    try:
        logger.info(
            f"started getting providerd for {product.name} {serviceprovider.lastname} at {datetime.now()}"
        )
        headers = {"Content-Type": "application/json","Authorization": serviceprovider.provider_auth}
        res = util.http(url=f'{serviceprovider.provider_url}services/bills/all-billers',headers=headers)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['status'] == "2000":
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse["data"]
            else:
                response["statuscode"] = "400"
                response["message"] = "failed"
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def electricityPackages(biller:ProductTypeModel):
    response = {}
    try:
        logger.info(
            f"started data plan request for {biller.billerName} {biller.provider.companyName} at {datetime.now()}"
        )
        headers = {"Content-Type": "application/json","Authorization": biller.provider.provider_auth}
        res = util.http(url=f'{biller.provider.provider_url}services/bills/all-billers',headers=headers)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['status'] == "2000":
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse["data"]
            else:
                response["statuscode"] = "400"
                response["message"] = "failed"
        else:
            response["statuscode"] = "400"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
