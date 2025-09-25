from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Enum,
    Numeric,Table,
    Text,
    DECIMAL,func,UniqueConstraint,Date, cast,
)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import timedelta
import uuid
from utils.constant import *

# from utils.database import Base
from enum import Enum as PythonEnum

Base = declarative_base()
class PriorityEnum(PythonEnum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
class WithrawalStatusEnum(PythonEnum):
    APPROVED = "approved"
    COMPLETED = "completed"
    WAITING = "waiting"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    FAILED = "failed"
class DebitStatusEnum(PythonEnum):
    APPROVE = "approved"
    INSUFICIENT = "insuficient Fund"
    ERROR = "Transaction Error"
    MERCHANT = "merchant"
    PROCESSING = "processing"
class TimeOfOperationEnum(PythonEnum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    EVENING = "Evening"
    NIGHT = "Night"
class TrainClassEnum(PythonEnum):
    FIRST = "first Class"
    BUSINESS = "Business Class"
    ADULT = "Standard Adult"
    MINOR = "Standard Minor"
class MovableEnum(PythonEnum):
    BIKE = "bike"
    TRICYCLE = "tricycle"
    CAR = "car"
    BUS = "bus"
    TRAIN = "train"
    AEROPLANE = "plane"
class AccountEnum(PythonEnum):
    INDIVIDUAL = "individual"
    AGENT = "agent"
    MERCHANT = "merchant"
    AGGREGATOR = "aggregator"
    BUSINESS = "business"
class AccountStatusEnum(PythonEnum):
    REG = "registration"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    LOCKED = "locked"
class AccountRatingEnum(PythonEnum):
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
class AccountType(PythonEnum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    revenue = "revenue"
    expense = "expense"
class CommissionType(PythonEnum):
    percentage = "percentage"
    calculated = "calculated"
class POSStatusEnum(PythonEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    LOCKED = "locked"
    REQUESTED = "requested"
    PAYMENT = "payment"
    APPROVED = "approved"
class AdminRoleEnum(PythonEnum):
    HEADOFFICE = "headoffice"
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    AUDIT = "audit"
    SUPPORT = "support"
    BUSINESS = "business"
    PROVIDER = "provider"
    BUSPROVIDER = "busprovider"
    TRAINPROVIDER = "trainprovider"
class AdminTypeEnum(PythonEnum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
class AdminStatusEnum(PythonEnum):
    ACTIVE = "active"
    NOTACTIVE = "notactive"
    PENDING = "pending"
class OTPStatusEnum(PythonEnum):
    SENT = "sent"
    PENDING = "pending"
    NOTSENT = "notsent"
    OPEN = "open"
    LOGGED = "logged"
    CLOSED = "closed"
class TransactionChannelEnum(PythonEnum):
    WEB = "web"
    MOBILE = "mobile"
    USSD = "ussd"
    POS = "pos"
class TransactionStatusEnum(PythonEnum):
    SUCCESS = "success"
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
class TransactionCodeEnum(PythonEnum):
    SUCCESS = "00"
    PENDING = "E01"
    PROCESSING = "E02"
    APPERROR = "E03"
    TIMEOUT = "E05"
    FAILED = "E100"
class PaymentEnum(PythonEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
class ChannelEnum(PythonEnum):
    MOBILE = "MOBILE"
    WEB = "WEB"
    PAYSTACK="PAYSTACK"
    WALLET="WALLET"
    CARD="CARD"
    NFC="NFC"
    QR="QR"
class TicketStatusEnum(PythonEnum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    USED = "used"
    EXPIRED = "expired"
class TicketModeEnum(PythonEnum):
    BUS = "bus"
    TRAIN = "train"
class RoleModel(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(25), nullable=False, default="Support")
    tag = Column(Enum(AdminRoleEnum), nullable=False, default=AdminRoleEnum.SUPPORT)
    description = Column(String(255))
    status = Column(Boolean, default=False)
    admins = relationship("AdminModel",  uselist=False,back_populates="role")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class AdminModel(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    billerId = Column(String(25),nullable=True, unique=True)
    firstname = Column(String(25))
    lastname = Column(String(25))
    phonenumber = Column(String(13))
    email = Column(String(255))
    password = Column(String(255), nullable=True)
    status = Column(Boolean, default=False)
    wallet = relationship("AccountModel",  uselist=False,back_populates="admin")
    role = relationship("RoleModel", back_populates="admins")
    cashouts = relationship("CashOutModel", backref="admin")
    user_notifications = relationship("UserNotification", back_populates="admin")
    preference = relationship('UserNotificationPreference', back_populates='admin')
    buses = relationship("BusModel", back_populates="provider")
    trains = relationship("TrainModel", back_populates="provider")
    support_tickets = relationship('SupportTicketModel', back_populates='admin')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(50),
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()).replace("-", ""),
    )
    firstname = Column(String(25))
    lastname = Column(String(25))
    middlename = Column(String(25))
    phonenumber = Column(String(13))
    gender = Column(Boolean, default=False)
    password = Column(String(255), nullable=True)
    pin = Column(String(255), nullable=True)
    email = Column(String(255),nullable=False)
    email_verified = Column(Boolean, default=False)
    date_of_birth = Column(String(13),nullable=True,default=f"{func.now()}")
    bvn = Column(String(12), nullable=True)
    nin = Column(String(13), nullable=True)
    state_of_origin = Column(String(50), nullable=True)
    state_of_residence = Column(String(50), nullable=True)
    lga_of_residence = Column(String(50), nullable=True)
    lga = Column(String(50), nullable=True)
    profile_picture = Column(LONGTEXT, nullable=True)
    photo = Column(LONGTEXT, nullable=True)
    residence_address = Column(String(255), nullable=True)
    marital_status = Column(String(50), nullable=True)
    name_on_card = Column(String(255), nullable=True)
    registration_date = Column(String(50), nullable=True)
    policy = Column(String(255), nullable=True)
    address_submitted = Column(Boolean, default=False)
    nin_submitted = Column(Boolean, default=False)
    referalcode = Column(String(13), nullable=True)
    bvn_verified = Column(Boolean, default=False)
    nin_verified = Column(Boolean, default=False)
    kyc_completed = Column(Boolean, default=False)
    cashout_enabled = Column(Boolean, default=False)
    cashout_account = Column(String(50), nullable=True)
    cashout_code = Column(String(50), nullable=True)
    cashout_bank = Column(String(50), nullable=True)
    cashout_limit = Column(String(50), default="10000000")
    commission_enabled = Column(Boolean, default=False)
    is_owner = Column(Boolean, default=True)
    is_next_of_kin = Column(Boolean, default=False)
    next_of_kin_name = Column(String(50), nullable=True)
    next_of_kin_address = Column(String(100), nullable=True)
    next_of_kin_phone = Column(String(13), nullable=True)
    next_of_kin_relationship = Column(String(25), nullable=True)
    aggrement = Column(String(100), nullable=True)
    authToken = Column(String(100), nullable=True)
    hasAuthToken = Column(Boolean, default=False)
    hideBalance = Column(Boolean, default=False)
    autoFund = Column(Boolean, default=False)
    autoFundThreshold = Column(String(50),default='0')
    autoFundAmount = Column(String(50),default='0')
    account_status = Column(
        Enum(AccountStatusEnum), nullable=False, default=AccountStatusEnum.REG
    )
    account_type = Column(
        Enum(AccountEnum), nullable=False, default=AccountEnum.INDIVIDUAL
    )
    account_ratings = Column(Enum(AccountRatingEnum), default=AccountRatingEnum.BRONZE)
    point_ratings = Column(String(13), default="5")
    # otps
    payments = relationship("PaymentModel", backref="user")
    # device
    device = relationship("DeviceModel", uselist=False, back_populates="user")
    # wallet
    wallet = relationship("AccountModel",  uselist=False,back_populates="user")
    # otps
    otps = relationship("OTPModel", backref="user")
    cards = relationship("CardsModel", backref="user")
    cashouts = relationship("CashOutModel", backref="user")
    # beneficiaries
    beneficiaries = relationship("BeneficiaryModel", backref="user")
    # notification
    user_notifications = relationship("UserNotification", back_populates="customer")

    #user_notifications = relationship("UserNotification", back_populates="customer")
    #notifications = relationship("NotificationModel", secondary="user_notifications", back_populates="users")
    preference = relationship('UserNotificationPreference', back_populates='user')
    # ticketing
    support_tickets = relationship('SupportTicketModel', back_populates='user')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class BeneficiaryModel(Base):
    __tablename__ = "beneficiaries"
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50))
    nickname = Column(String(100))
    customerId = Column(String(50))
    billercode = Column(String(20))
    billername = Column(String(255), nullable=True)
    logo = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("customers.id"))
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class OTPModel(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    otp = Column(String(6))
    servicename = Column(String(255))
    status = Column(Enum(OTPStatusEnum), nullable=False, default=OTPStatusEnum.OPEN)
    user_id = Column(Integer, ForeignKey("customers.id"))
    #user = relationship("CustomerModel", back_populates="otps")
    created_at = Column(DateTime, default=func.now())
    expired_at = Column(
        DateTime,
        default=func.now() + timedelta(minutes=15),
    )
    updated_at = Column(DateTime, default=func.now())
class CardsModel(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("customers.id"))
    authorization_code = Column(String(100))
    bin= Column(String(50),default='0')
    last4= Column(String(5),nullable=True)
    exp_month= Column(String(3),nullable=True)
    exp_year= Column(String(5),nullable=True)
    channel= Column(String(10),nullable=True)
    card_type= Column(String(25),nullable=True)
    bank= Column(String(25),nullable=True)
    signature= Column(String(25),nullable=True)
    account_name= Column(String(25),nullable=True)
    reusable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class AccountModel(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("customers.id"),nullable=True)
    admin_id = Column(Integer, ForeignKey("admins.id"),nullable=True)
    user = relationship("CustomerModel", back_populates="wallet")
    admin = relationship("AdminModel", back_populates="wallet")
    payments = relationship('PaymentModel', backref='wallet')
    walletAccount = Column(String(11))
    availableBalance= Column(String(50),default='0')
    referenceNo= Column(String(11),nullable=True)
    accountStatus = Column(Enum(AccountStatusEnum), nullable=False, default=AccountStatusEnum.ACTIVE)
    #accountStatus= Column(String(20),default=AccountStatusEnum.ACTIVE)
    cashout_enabled = Column(Boolean, default=False)
    cashout_account = Column(String(50), nullable=True)
    cashout_code = Column(String(50), nullable=True)
    cashout_bank = Column(String(50), nullable=True)
    cashout_limit = Column(String(50), default="10000000")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class CashOutModel(Base):
    __tablename__ = "cashouts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("customers.id"),nullable=True)
    admin_id = Column(Integer, ForeignKey("admins.id"),nullable=True)
    #payment = relationship('PaymentModel', backref='cashout')
    source= Column(String(50),default='balance')
    amount= Column(String(20),default='0')
    recipient= Column(String(50),nullable=False)
    withdrawalStatus =  Column(Enum(WithrawalStatusEnum), nullable=False, default=WithrawalStatusEnum.WAITING)
    statusCode =  Column(Enum(TransactionCodeEnum), nullable=False, default=TransactionCodeEnum.PROCESSING)
    statusDescription =  Column(Enum(TransactionStatusEnum), nullable=False, default=TransactionStatusEnum.PROCESSING)
    reference = Column(String(100),nullable=False,unique=True, default=lambda: str(uuid.uuid4()),)
    reason = Column(String(220),nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class DeviceModel(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    platformVersion = Column(String(255))
    imeiNo = Column(String(255))
    modelName = Column(String(255))
    manufacturer = Column(String(255))
    isPhysicalDevice = Column(String(255))
    deviceName = Column(String(255))
    apiLevel = Column(String(255))
    user_id = Column(Integer, ForeignKey("customers.id"), unique=True)
    user = relationship("CustomerModel", back_populates="device")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    description = Column(String(255), nullable=True)
    vasType = Column(String(50))
    icon = Column(String(55), nullable=True)
    customerField = Column(String(20), nullable=True)
    status = Column(Boolean, default=False)
    billers = relationship("ProductTypeModel", backref="product")
    payments = relationship('PaymentModel',back_populates='product')
    #iswId = Column(String(20), nullable=True)
    enabledInline = Column(Boolean, default=False)
    isWeb = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class ProductTypeModel(Base):
    __tablename__ = "product_types"
    id = Column(Integer, primary_key=True, index=True)
    billerName = Column(String(50))
    billerId = Column(String(15))
    #paymentCode = Column(String(25), default="90501")
    #paydirectItemCode = Column(String(25), default="01")
    billerType = Column(String(25))
    #iswCatId = Column(String(20), nullable=True)
    #iswBillerId = Column(String(20), nullable=True)
    #iswPayDirectProductId = Column(String(20), nullable=True)
    amountType = Column(String(20), nullable=True)
    #product = relationship("ProductModel", back_populates="products")
    logo = Column(String(255), nullable=True)
    customerField = Column(String(255))
    provider = Column(String(10),default="ISW")
    network = Column(String(255), nullable=True)
    vat = Column(Integer, default=0)
    maxAmountLimit = Column(Integer, default=500000)
    minAmountLimit = Column(Integer, default=5000)
    status = Column(Boolean, default=False)
    hasPackages = Column(Boolean, default=False)
    hasLookup = Column(Boolean, default=False)
    hasAddons = Column(Boolean, default=False)
    currencyCode = Column(String(25), default="566")
    currencySymbol = Column(String(25), default="NGN")
    product_id = Column(Integer, ForeignKey("products.id"))
    packages = relationship("PackageModel", backref="product_type")
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class PackageModel(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    product_type_id = Column(Integer, ForeignKey("product_types.id"))
    #biller = relationship("ProductTypeModel", back_populates="packages")
    billerId = Column(String(15))
    description = Column(String(150))
    amount = Column(String(50), default='0')
    validity = Column(String(50), nullable=True)
    packageCode = Column(String(50))
    #paymentCode = Column(String(25), default="90501")
    #paydirectItemCode = Column(String(25), default="01")
    currencyCode = Column(String(25), default="566")
    currencySymbol = Column(String(25), default="NGN")
    status = Column(Boolean, default=False)
    hasValidity = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class TransactionModel(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("customers.id"))
    terminalId = Column(String(25), nullable=True)
    transactionId = Column(String(255), default=uuid.uuid4())
    channel = Column(
        Enum(TransactionChannelEnum),
        nullable=False,
        default=TransactionChannelEnum.MOBILE,
    )
    status = Column(
        Enum(TransactionStatusEnum),
        nullable=False,
        default=TransactionStatusEnum.PENDING,
    )
    isDebit = Column(Boolean, default=True)
    remarks = Column(String(255), nullable=True)
    reference = Column(String(255), nullable=True)
    customerBillerId = Column(String(255), nullable=True)
    amount = Column(String(255), nullable=True)
    product = Column(String(255), nullable=True)
    transactionType = Column(String(255), nullable=True)
    transactionStatus = Column(String(255), nullable=True)
    recipientId = Column(String(255), nullable=True)
    recipientAccountNumber = Column(String(255), nullable=True)
    recipientBank = Column(String(255), nullable=True)
    recipientName = Column(String(255), nullable=True)
    senderName = Column(String(255), nullable=True)
    cardRRN = Column(String(255), nullable=True)
    cardPan = Column(String(255), nullable=True)
    provider = Column(String(255), nullable=True)
    btcode = Column(String(5), nullable=True)
    cashbackFee = Column(DECIMAL(10, 2), default=0.0)
    serviceFee = Column(DECIMAL(10, 2), default=0.0)
    accountImpacted = Column(Boolean,default=False)
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class PaymentModel(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('wallets.id'), nullable=False)
    user_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    cashout_id = Column(Integer, ForeignKey("cashouts.id"),nullable=True)
    code = Column(String(20), ForeignKey("gl_accounts.code"))
    amount = Column(String(50), nullable=False)
    reference = Column(String(100),nullable=False,unique=True, default=lambda: str(uuid.uuid4()),)
    transactionreference = Column(String(100), nullable=True)
    access_code = Column(String(100), nullable=True)
    event = Column(String(100), nullable=True)
    paystack_id = Column(String(100), nullable=True)
    status = Column(String(25), nullable=True)
    statusMessage = Column(String(200), nullable=True)
    payment_date = Column(String(25), nullable=False,default=cast(func.now(), Date))
    fee = Column(String(25), default='0')
    recipient = Column(String(50), nullable=False)
    providerAmount = Column(String(50), nullable=True,default='0')
    commissionAmount = Column(String(50), nullable=True,default='0')
    payment_type = Column(Enum(PaymentEnum), nullable=False, default=PaymentEnum.DEBIT)
    channel =  Column(Enum(ChannelEnum), nullable=False, default=ChannelEnum.MOBILE)
    statusCode =  Column(Enum(TransactionCodeEnum), nullable=False, default=TransactionCodeEnum.PROCESSING)
    statusDescription =  Column(Enum(TransactionStatusEnum), nullable=False, default=TransactionStatusEnum.PROCESSING)
    balanceBefore = Column(String(25), default='0')
    balanceAfter = Column(String(25), default='0')
    product_id = Column(Integer, ForeignKey('products.id'))
    product = relationship("ProductModel",  back_populates="payments")
    product_type_id = Column(Integer, ForeignKey('product_types.id'))
    productType = relationship("ProductTypeModel", backref="product_types")
    cashout_id = Column(Integer, ForeignKey('cashouts.id'))
    cashout = relationship("CashOutModel", backref="cashouts")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class BankModel(Base):
    __tablename__ = "banks"
    id = Column(Integer, primary_key=True, index=True)
    cbnCode = Column(String(10))
    shortname = Column(String(10))
    longname = Column(String(255))
    status = Column(Boolean, default=False)
    code = Column(String(5), nullable=True)
    nubancode = Column(String(10), nullable=True)
    sortcode = Column(String(10), nullable=True)
    ussdCode = Column(String(50), nullable=True)
    meta1 = Column(String(100), nullable=True)
    meta2 = Column(String(100), nullable=True)
    logo = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class SettingsModel(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    app_name = Column(String(255), default="SMART TAP API")
    channel_name = Column(String(50), default="smart_tap")
    debug = Column(Boolean, default=True)
    db_url = Column(String(100), default="")
    mail_username = Column(String(100), nullable=True)
    mail_password = Column(String(250), nullable=True)
    mail_from = Column(String(80), nullable=True)
    mail_port = Column(String(9), nullable=True)
    mail_server = Column(String(150), nullable=True)
    mail_from_name = Column(String(100), nullable=True)
    mail_token  = Column(String(250), nullable=True)
    allowed_hosts = Column(String(255), nullable=True)
    allowed_origins = Column(String(255), nullable=True)
    access_token_expire_minutes = Column(Integer, nullable=True)
    secret_key = Column(String(250), nullable=True)
    algorithm = Column(String(250), nullable=True)
    vanso_url = Column(String(250), nullable=True)
    vanso_username = Column(String(250), nullable=True)
    vanso_password = Column(String(250), nullable=True)
    senderid = Column(String(250), nullable=True)
    isw_qa_url = Column(String(250), nullable=True)
    isw_qa_terminalid = Column(String(250), nullable=True)
    isw_qa_clientid = Column(String(250), nullable=True)
    isw_qa_secret = Column(String(250), nullable=True)
    isw_k8_url = Column(String(250), nullable=True)
    focus_code = Column(String(8), default="0093")
    paystack_url = Column(String(250), nullable=True)
    paystack_token = Column(String(250), nullable=True)
    gl_cust = Column(String(25), nullable=True)
    cust_gl = Column(String(25), nullable=True)
    gl_inflow= Column(String(25), nullable=True)
    gl_outflow= Column(String(25), nullable=True)
    gl_com= Column(String(25), nullable=True)
    gl_payable= Column(String(25), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), default="APP")
    title = Column(String(150), nullable=False)
    message = Column(Text, default='0')
    isRead = Column(Boolean, default=False)
    user_notifications = relationship("UserNotification", back_populates="notification",cascade="all, delete",passive_deletes=True )
    #users = relationship('CustomerModel', secondary='user_notifications', back_populates='notifications')
    #user_notifications = relationship('UserNotification', back_populates='notification')
    updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
class UserNotificationPreference(Base):
    __tablename__ = 'user_notification_preferences'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    #notification_type_id = Column(Integer, ForeignKey('notification_types.id'), nullable=False)
    receive_via_email = Column(Boolean, default=True)
    receive_via_sms = Column(Boolean, default=False)
    receive_in_app = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    user = relationship('CustomerModel', back_populates='preference')
    admin = relationship('AdminModel', back_populates='preference')
    #notification_type = relationship('NotificationType')
class UserNotification(Base):
    __tablename__ = 'user_notifications'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    notification_id = Column(Integer, ForeignKey('notifications.id', ondelete="CASCADE"), nullable=False,)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    customer = relationship("CustomerModel", back_populates="user_notifications")
    admin = relationship("AdminModel", back_populates="user_notifications")
    notification = relationship("NotificationModel", back_populates="user_notifications")

    #customer = relationship("CustomerModel", back_populates="user_notifications")
    #notification = relationship('NotificationModel', back_populates='user_notifications')
class SupportTicketModel(Base):
    __tablename__ = 'support_tickets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  # Creator of the ticket
    user = relationship('CustomerModel', back_populates='support_tickets')
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True)  # Assigned support agent
    admin = relationship("AdminModel",  back_populates="support_tickets")
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.INFO) 
    status = Column(Enum(OTPStatusEnum), default=OTPStatusEnum.OPEN) 
    attachment = Column(Text, nullable=True)
    comments = relationship('TicketCommentModel', backref='support_ticket', cascade='all, delete-orphan')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class TicketCommentModel(Base):
    __tablename__ = 'ticket_comments'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('support_tickets.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  # Comment author
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True)
    comment = Column(Text, nullable=False)
    attachment = Column(Text, nullable=True)
    #attachments = relationship('TicketAttachmentModel', backref='ticket_comments', cascade='all, delete-orphan')
    created_at = Column(DateTime, default=func.now())
    user = relationship('CustomerModel', backref='comments')
    agent = relationship('AdminModel', backref='comments')
class TicketAttachmentModel(Base):
    __tablename__ = 'ticket_attachments'
    
    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey('ticket_comments.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    uploaded_by = Column(Integer, ForeignKey('customers.id'), nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    user = relationship('CustomerModel', backref='attachments')
class LoanModel(Base):
    __tablename__ = 'loans'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    loan_type_id = Column(Integer, ForeignKey('loan_types.id'), nullable=False)
    principal_amount = Column(String(50), nullable=False)  # Original loan amount
    interest_rate = Column(String(50), nullable=False)  # Annual interest rate
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status_id = Column(Integer, ForeignKey('loan_statuses.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    type = relationship('LoanTypeModel', backref='loans')
    user = relationship('CustomerModel', backref='loans')
    status = relationship('LoanStatusModel', backref='loans')
class LoanTypeModel(Base):
    __tablename__ = 'loan_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class LoanStatusModel(Base):
    __tablename__ = 'loan_statuses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class TrainScheduleModel(Base):
    __tablename__ = 'train_schedule'
    
    id = Column(Integer, primary_key=True)
    train_id = Column(Integer, ForeignKey('trains.id'), nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
class BusScheduleModel(Base):
    __tablename__ = 'bus_schedule'
    
    id = Column(Integer, primary_key=True)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
class ScheduleSeatModel(Base):
    __tablename__ = 'seat_schedule'
    
    id = Column(Integer, primary_key=True)
    seat_id = Column(Integer, ForeignKey('seats.id'), nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
class TrainSeatModel(Base):
    __tablename__ = 'seat_train'
    id = Column(Integer, primary_key=True)
    seat_id = Column(Integer, ForeignKey('seats.id'), nullable=False)
    train_id = Column(Integer, ForeignKey('trains.id'), nullable=False)
class SeatModel(Base):
    __tablename__ = 'seats'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    #train_id  = Column(Integer, ForeignKey("trains.id"))
    trains =  relationship("TrainModel", secondary="seat_train", back_populates="seats",cascade="all")
    #schedule_id  = Column(Integer, ForeignKey("schedules.id"))
    #schedules =  relationship("ScheduleModel", secondary="seat_schedule", back_populates="seats")
    seatNumber = Column(String(50), nullable=False)
    price = Column(String(25), nullable=True)
    classType = Column(Enum(TrainClassEnum), default=TrainClassEnum.ADULT)
    availabilityStatus = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class ParkModel(Base):
    __tablename__ = 'parks'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    name = Column(String(150), nullable=False)
    parkImage = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    contact = Column(String(50), nullable=True)
    startingPoint = Column(String(100), nullable=True)
    destination = Column(String(100), nullable=True)
    price = Column(String(25), nullable=True)
    estimatedDeparture = Column(DateTime, nullable=True)
    estimatedArrival = Column(DateTime,nullable=True)
    description = Column(String(255), nullable=True)
    policy = Column(String(255), nullable=True)
    status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class StationModel(Base):
    __tablename__ = 'stations'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    stationName = Column(String(50), nullable=False, unique=True)
    location = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    parkImage = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    contact = Column(String(50), nullable=True)
    policy = Column(String(255), nullable=True)
    status = Column(Boolean, default=False)
    mode= Column(Enum(TicketModeEnum), default=TicketModeEnum.BUS)  # schedule mode
    depature = relationship("RouteModel", foreign_keys="RouteModel.sourceStation_id", back_populates="sourceStation")
    arrival = relationship("RouteModel", foreign_keys="RouteModel.destinationStation_id", back_populates="destinationStation")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
bus_route = Table('bus_route',
    Base.metadata,
    Column('bus_id', Integer, ForeignKey('buses.id' ,ondelete="CASCADE"), primary_key=True),
    Column('route_id', Integer, ForeignKey('routes.id',ondelete="CASCADE"), primary_key=True)
)
train_route = Table('train_route',
    Base.metadata,
    Column('train_id', Integer, ForeignKey('trains.id',ondelete="CASCADE"), primary_key=True),
    Column('route_id', Integer, ForeignKey('routes.id',ondelete="CASCADE"), primary_key=True)
)
class BusModel(Base):
    __tablename__ = 'buses'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    name = Column(String(100), nullable=False, unique=True)
    seatCount = Column(Integer)
    bus_number = Column(String(10),)
    park_id = Column(Integer, ForeignKey("parks.id"))
    billerId = Column(String(25),nullable=True)
    description = Column(String(255), nullable=True)
    types = Column(Enum(MovableEnum), nullable=False, default=MovableEnum.BUS)
    airCondition = Column(Boolean, default=False)
    camera = Column(Boolean, default=False)
    tv = Column(Boolean, default=False)
    base_price = Column(String(25), nullable=True)
    availabilityStatus = Column(Boolean, default=False)
    busImage = Column(String(255), nullable=True)
    routes = relationship('RouteModel',secondary=bus_route,back_populates='buses',cascade="all")
    park = relationship("ParkModel", backref="buses")
    provider = relationship("AdminModel", back_populates="buses")
    schedules =  relationship("ScheduleModel", secondary="bus_schedule", back_populates="buses")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class RouteModel(Base):
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True)
    routeName = Column(String(50), nullable=True,)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    mode= Column(Enum(TicketModeEnum), default=TicketModeEnum.BUS)  # schedule mode
    sourceStation_id = Column(Integer, ForeignKey("stations.id"))
    destinationStation_id = Column(Integer, ForeignKey("stations.id"))
    sourceStation = relationship("StationModel", foreign_keys=[sourceStation_id], back_populates="depature")
    destinationStation = relationship("StationModel", foreign_keys=[destinationStation_id], back_populates="arrival")
    trains = relationship('TrainModel',secondary=train_route,back_populates='routes',cascade="all")
    buses = relationship('BusModel',secondary=bus_route,back_populates='routes',cascade="all")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class TrainModel(Base):
    __tablename__ = 'trains'
    
    id = Column(Integer, primary_key=True)
    trainNumber = Column(String(50), nullable=False, unique=True)
    trainName = Column(String(50), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    image = Column(String(255), nullable=True)
    billerId = Column(String(25),nullable=True)
    provider = relationship("AdminModel", back_populates="trains")
    routes = relationship('RouteModel',secondary=train_route,back_populates='trains',cascade="all")
    schedules =  relationship("ScheduleModel", secondary="train_schedule", back_populates="trains")
    seats = relationship('SeatModel',secondary="seat_train",back_populates='trains',cascade="all")
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class ScheduleModel(Base):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=True,default=0)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=True)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=True)
    #route_id = Column(Integer, ForeignKey('routes.id'), nullable=False)
    departureTime = Column(String(50), nullable=False)
    arrivalTime = Column(String(255), nullable=True)
    #seats =  relationship("SeatModel", secondary="seat_schedule", back_populates="schedules")
    daysOfOperation = Column(String(255), nullable=True)
    timeOfOperation = Column(Enum(TimeOfOperationEnum), default=TimeOfOperationEnum.MORNING)
    mode= Column(Enum(TicketModeEnum), default=TicketModeEnum.BUS)  # schedule mode
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    trains = relationship("TrainModel", secondary="train_schedule", back_populates="schedules")
    buses = relationship("BusModel", secondary="bus_schedule", back_populates="schedules")
class TicketModel(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False,default=0)
    customer = relationship('CustomerModel', backref='tickets')
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=True)
    train_id = Column(Integer, ForeignKey('trains.id'), nullable=True)
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=True)
    seat_id = Column(Integer, ForeignKey('seats.id'), nullable=True)
    bus = relationship('BusModel', backref='tickets')
    train = relationship('TrainModel', backref='tickets')
    route = relationship('RouteModel', backref='tickets')
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)  # Train schedule
    schedule = relationship('ScheduleModel', backref='tickets')
    ticket_number =  Column(String(50), unique=True)
    seat_number = Column(String(50), nullable=True)  # Seat number
    price= Column(String(25), nullable=True)  # Ticket price
    qr_code = Column(String(255), nullable=False,unique=True)  # QR code string or URL
    status= Column(Enum(TicketStatusEnum), default=TicketStatusEnum.BOOKED)  # Ticket status
    mode= Column(Enum(TicketModeEnum), default=TicketModeEnum.BUS)  # Ticket status
    booked_at = Column(DateTime, default=func.now())  
    expired_at = Column(DateTime, default=func.now())# Purchase time
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
class GLAccountModel(Base):
    __tablename__ = "gl_accounts"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    gl_type = Column(Enum(AccountType), nullable=False)
    gl_balance = Column(String(20), nullable=False,default='0')
    journal_entries = relationship('JournalEntryModel', backref='gl_account')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(),onupdate=func.now())
class JournalEntryModel(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), ForeignKey("gl_accounts.code"))
    #gl_account = relationship('GLAccountModel', backref='journal_entries')
    admin_id = Column(Integer, ForeignKey("admins.id"))
    amount = Column(String(20), nullable=False)
    is_debit = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(),onupdate=func.now())
class ServiceRateModel(Base):
    __tablename__ = "service_rates"
    id = Column(Integer, primary_key=True)
    gl_to_provider = Column(String(20), ForeignKey("gl_accounts.code"))
    provider_to_gl = Column(String(20), ForeignKey("gl_accounts.code"))
    admin_id = Column(Integer, ForeignKey("admins.id"))
    admin = relationship('AdminModel', backref='service_rates')
    product_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="CASCADE"))
    product_type = relationship('ProductTypeModel', backref='service_rates')
    provider_discount_rate = Column(Numeric(7, 2), nullable=False)
    provider_discount_type = Column(Enum(CommissionType), nullable=False)
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=func.now(),onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
class CommissionModel(Base):
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True)
    product_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="CASCADE"))
    product_type = relationship('ProductTypeModel', backref='commissions')
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="CASCADE"))
    admin = relationship('AdminModel', backref='commissions')
    glcode = Column(String(20), ForeignKey("gl_accounts.code"))
    commission_rate = Column(Numeric(7, 2), nullable=False)
    commission_type = Column(Enum(CommissionType), nullable=False)
    updated_at = Column(DateTime, default=func.now(),onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    __table_args__ = (
        UniqueConstraint('admin_id', 'product_type_id', name='uix_admin_product_type'),
    )