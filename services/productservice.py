
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import productQuery
from utils.constant import *
from schemas.customer import *

logger = logging.getLogger(__name__)


def getAllBill(db: Session):
    bills = productQuery.get_all_bill(db=db)
    logger.info(bills)
    return bills


def getSingleBill(db: Session, id: int):
    bill = productQuery.get_single_bill_by_id(db=db, id=id)
    logger.info(bill)
    return bill


def getAllBillers(db: Session):
    bills = productQuery.get_all_biller(db=db)
    logger.info(bills)
    return bills


def getSingleBiller(db: Session, id: int):
    bill = productQuery.get_single_biller_by_id(db=db, id=id)
    logger.info(bill)
    return bill