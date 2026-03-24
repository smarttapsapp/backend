
from sqlalchemy.orm import Session
from models.model import *
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)


def get_all_bill(db: Session):
    return db.query(ProductModel).filter(ProductModel.status == True).filter(ProductModel.isWeb == True).all()
def get_single_bill_by_id(db: Session, id: int):
    return db.query(ProductModel).filter(ProductModel.id == id).filter(ProductModel.status == True).first()
def get_all_biller(db: Session):
    return db.query(ProductTypeModel).filter(ProductTypeModel.status == True).all()
def get_single_biller_by_id(db: Session, id: int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.id == id).first()
def get_single_biller_by_billerId(db: Session, billerId: str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerId == billerId).first()
def query_bus_routes(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_no_type(db: Session, departure: str, arrival: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_departure(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_bus_routes_arrival(db: Session, departure: str, arrival: str, searchType: str):
    return db.query(ParkModel).filter(ParkModel.address.like(f"%{departure}%")).filter(ParkModel.address.like(f"%{arrival}%")).all()
def query_stations(db: Session):
    return db.query(StationModel).all()
def query_train_routes(db: Session, departure: str, arrival: str, seatType: str, takeOffTime: str):
    return db.query(RouteModel).filter(RouteModel.mode == TicketModeEnum.TRAIN).all()
def querySinglebeneficiary(db: Session,transactionType:str,userId:int, customerId: str):
    return db.query(BeneficiaryModel).filter(BeneficiaryModel.user_id == userId).filter(BeneficiaryModel.customerId == customerId).filter(BeneficiaryModel.transaction_type == transactionType).first()
def queryBeneficiaryByTransactionType(db: Session,transactionType:str,userId:int):
    return db.query(BeneficiaryModel).filter(BeneficiaryModel.user_id == userId).filter(BeneficiaryModel.transaction_type == transactionType).all()
def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
def deleteRecord(db:Session,id:int,userId:int):
    return db.query(BeneficiaryModel).filter(BeneficiaryModel.id == id).filter(BeneficiaryModel.user_id == userId).delete()
def getProducts(db: Session):
    return db.query(ProductModel).all()
def getProductById(db: Session,productId:int):
    return db.query(ProductModel).filter(ProductModel.id == productId).first()
def deleteProduct(db: Session ,productId:int):
    deleted = db.query(ProductModel).filter(ProductModel.id == productId).delete()
    if deleted:
        db.commit()
        return True
    return False
def getProductBillers(db: Session):
    return db.query(ProductTypeModel).filter(ProductTypeModel.status == True).order_by(desc(ProductTypeModel.created_at)).all()
def getBillers(db: Session):
    return db.query(ProductTypeModel).order_by(desc(ProductTypeModel.created_at)).all()
def getProductTypeById(db: Session,billerId:int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.id == billerId).first()
def getBillersByProductId(db: Session,productId:int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.product_id == productId).order_by(desc(ProductTypeModel.created_at)).all()
def deleteBiller(db: Session ,billerId:int):
    deleted = db.query(ProductTypeModel).filter(ProductTypeModel.id == billerId).delete()
    if deleted:
        db.commit()
        return True
    return False
def getPackages(db: Session):
    return db.query(PackageModel).order_by(desc(PackageModel.created_at)).all()
def getPackageById(db: Session,packageId:int):
    return db.query(PackageModel).filter(PackageModel.id == packageId).first()
def getPackagesByBillerId(db: Session,billerId:int):
    return db.query(PackageModel).filter(PackageModel.product_type_id == billerId).order_by(desc(PackageModel.created_at)).all()
def deletePackage(db: Session ,packageId:int):
    deleted = db.query(PackageModel).filter(PackageModel.id == packageId).delete()
    if deleted:
        db.commit()
        return True
    return False
def getProductTypeByBiller(db: Session,billerId:str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerId == billerId).first()
def getPackageByPaymentCode(db: Session,code:str):
    return db.query(PackageModel).filter(PackageModel.packageCode == code).first()
def getServiceProviderById(db: Session,id:int):
    return db.query(AdminModel).filter(AdminModel.id == id).first()
def getDiscountProviderProductType(db: Session,providerId:int,productTypeId:int):
    return db.query(ServiceRateModel).filter(ServiceRateModel.admin_id == providerId,ServiceRateModel.product_type_id ==productTypeId).first()