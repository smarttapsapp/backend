from sqlalchemy.orm import Session
from sqlalchemy import desc,or_
from sqlalchemy.sql import select,update
from models.model import *
from schemas.account import Account
import logging

logger = logging.getLogger(__name__)



def userByEmailOrPhone(db: Session, email: str,phonenumber:str):
    return db.query(CustomerModel).filter(or_(CustomerModel.email == email, CustomerModel.phonenumber == phonenumber)).first()
def get_latest_otp(db: Session, userId: int):
    return db.query(OTPModel).filter(OTPModel.user_id == userId).filter(OTPModel.status == OTPStatusEnum.OPEN).order_by(desc(OTPModel.id)).first()
def get_otp_by_code(db: Session,code:str, userId: int):
    return db.query(OTPModel).filter(OTPModel.otp == code).filter(OTPModel.user_id == userId).filter(OTPModel.status == OTPStatusEnum.OPEN).first()
def otpViaCodeAndServicename(db: Session,code:str,servicename:str,userId: int):
    return db.query(OTPModel).filter(OTPModel.otp == code).filter(OTPModel.user_id == userId).filter(OTPModel.status == OTPStatusEnum.OPEN).filter(OTPModel.servicename == servicename).first()


def getCheckAdmin(db: Session, username: str):
    return db.query(AdminModel).filter(AdminModel.email == username).first()
def queryAllAdminUsers(db: Session):
    return db.query(AdminModel).all()


def get_user_bvn(db: Session, bvn: str):
    return db.query(CustomerModel).filter(CustomerModel.bvn == bvn).first()



def get_user_by_id(id: int, db: Session):
    return db.query(CustomerModel).filter(CustomerModel.id == id).first()
def create_account(db: Session, user: CustomerModel):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
def create_otp(db: Session, otp: OTPModel):
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return otp
def create_wallet(db: Session, wallet: Account):
    stmt = (select(Account).where(Account.nuban == wallet.nuban))
    existWallet = db.execute(statement=stmt).first()
    if existWallet:
        return existWallet
    db.add(Account(**wallet.model_dump()))
    db.commit()
    db.refresh(wallet)
    return wallet
def updateUser(db: Session, userId: int,customerId:str,bankoneId:str):
    stmt = (update(CustomerModel)
            .where(CustomerModel.id == userId)
            .values(
                updated_at=datetime.now(),
                account_status= AccountStatusEnum.ACTIVE,
                bvn_verified=True,
                customerId=customerId,
                    bankOneId=bankoneId
                    )
            .execution_options(synchronize_session="fetch"))
    res = db.execute(statement=stmt)
    db.commit()
    return  res 
def updateOTPStatus(db: Session, id: int):
    stmt = (update(OTPModel)
            .where(OTPModel.id == id)
            .values(updated_at=datetime.now(),
                    status=OTPStatusEnum.CLOSED,
                    )
            .execution_options(synchronize_session="fetch"))
    res = db.execute(statement=stmt)
    db.commit()
    return  res 
def getAccountByUserId(id: int, db: Session):
    return db.query(Account).filter(Account.user_id == id).order_by(desc(Account.created_at)).first()

