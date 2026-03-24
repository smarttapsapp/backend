

import logging
from utils import util
from models.model import *
from datetime import datetime
from schemas.setting import Setting
logger = logging.getLogger(__name__)

async def purchaseService(biller:ProductTypeModel, serviceprovider:AdminModel,params: dict = None):
    response = {}
    try:
        logger.info(f"started sending request to {serviceprovider.firstname} at {datetime.now()}")
        if str(biller.billerType).lower() == 'airtime':
            providerUrl = f"{serviceprovider.provider_url}/{biller.billerId}/airtime"
        elif str(biller.billerType).lower() == 'data':
            providerUrl = f"{serviceprovider.provider_url}/{biller.billerId}/data"
        elif biller.billerType == 'electricity':
            providerUrl = f"{serviceprovider.provider_url}/{biller.billerId}/electricity"
        elif biller.billerType == 'cable':
            providerUrl = f"{serviceprovider.provider_url}/{biller.billerId}/cable"
        header = {"Content-Type": "application/json","Authorization": serviceprovider.provider_auth}
        res = util.http(url=providerUrl,params=params,headers=header)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse["status"] == "2000":
                response["statusCode"] = "200"
                response["tranxReference"] = jsonresponse["referenceNumber"]
                response["confirmCode"] = jsonresponse["confirmationCode"]
                response["mReference"] = jsonresponse["correlationId"]
                response["statusDescription"] = jsonresponse["message"]
                response["amount"] = jsonresponse["amount"]
            elif jsonresponse["status"] == "5010":
                response["statusCode"] = "C001"
                response["tranxReference"] = jsonresponse["referenceNumber"]
                response["statusDescription"] = jsonresponse["message"]
            else:
                response["statusCode"] = "C13"
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

async def billEnquriesService(setting: Setting,biller:ProductTypeModel, serviceprovider:AdminModel,params: dict = None):
    response = {}
    try:
        logger.info(
            f"started sending request to {serviceprovider.provider_name} at {datetime.now()}"
        )
        if serviceprovider.provider_code == '001':
            params['key'] = serviceprovider.service_key
            params['loginId'] =  serviceprovider.login_id
        res = util.http(url=f'{serviceprovider.provider_url}validate',params=params,method=serviceprovider.auth_method)
        jsonresponse = res.json()
        if res.status_code == 200:
            if jsonresponse['statusCode'] in ["00","C001"]:
                response["statuscode"] = "200"
                response["message"] = SUCCESS
                response["data"] = jsonresponse
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
