from models.model import *
from sqlalchemy.orm import Session
from models.queries import adminQuery
def calculate_agent_commission(db:Session,adminId: int, productTypeId: int, amount: str):
    commission = adminQuery.getServiceCommissionByProduct(db=db,productTypeId=productTypeId,adminId=adminId)
    if commission:
        if commission.commission_type == CommissionType.percentage:
            return round(int(amount) * commission.commission_rate, 2)
        return  int(amount) - (int(amount) - commission.commission_rate)
    return 0.0
def calculate_provider_discount(db:Session,productTypeId: int, amount: str):
    discount = adminQuery.getServiceProviderByProduct(db=db,productTypeId=productTypeId)
    if discount:
        if discount.provider_discount_type == CommissionType.percentage:
            return int(amount) * discount.provider_discount_rate
        return  int(amount) - (int(amount) - discount.provider_discount_rate)
    return 0
