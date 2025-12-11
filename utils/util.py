import requests
import re
import locale
from random import randint
import uuid
import logging
import json
import secrets
import base64
import bcrypt
from functools import lru_cache
from typing import Union
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi import BackgroundTasks
from enum import Enum as PythonEnum
from geopy.geocoders import Nominatim
from jose import jwt, JWTError
from passlib.context import CryptContext
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from schemas.setting import Setting,AppSetting
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates/email")
templates.env.globals['now'] = datetime.now
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_response(url,method=None,body=None,headers=None,status_code=500, message="Service Unavailable"):
    response = requests.Response()
    headers = headers or {"content-type": "application/json"}
    method = method or "GET"
    request = requests.Request(method, url, headers=headers, data=body).prepare()
    response.status_code = status_code
    response._content = json.dumps({"statusCode":str(status_code),"statusDescription":message,}).encode()  # Encode message as bytes
    response.headers = headers
    response.request = request
    return response
def http(url, params={}, headers={"content-type": "application/json"},contentType="json",method="GET",files=None,timeout=10):
    print("INFO|%s|%s|%s" % (str(http.__name__), str(url), str(params)))
    startTime = datetime.now()
    try:
        if len(params) > 0:
            if contentType =="formData":
                print("am here")
                resp = requests.post(url, data = params,files=files,timeout=timeout)
            else:
                resp = requests.post(url, data = json.dumps(params), headers=headers, timeout=timeout)
        else:
            if method=="POST":
                resp = requests.post(url,headers=headers,timeout=timeout)
            else:
                resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.Timeout:
        print("Request timed out.")
        resp =  create_response(url=url,method=method,body=params,headers=headers,status_code=408,message="Request timed out.")
    except requests.ConnectionError:
        print("Connection error.")
        resp =  create_response(url=url,method=method,body=params,headers=headers,status_code=503,message="Connection error try again later")
    except requests.RequestException as e:
        resp = create_response(url=url,method=method,body=params,headers=headers,status_code=500,message="System busy try again later")
    endTime = datetime.now()
    responseTime = (endTime - startTime).total_seconds()
    text = "_URL:: %s,_HEADER:: %s, _PARAM:: %s, _RESPONSE:: %s _STATUSCODE:: %s _TIME:: %s " % (
        str(resp.request.url),
        str(resp.request.headers),
        str(resp.request.body),
        str(resp.content),
        str(resp.status_code),
        str(responseTime),
    )
    print(text)
    return resp
def sendMail(setting: Setting, subject: str, toAddress: str,body=None, templatekey=None,template_data=None):
    try:
        headers = {'accept': "application/json",'content-type': "application/json",'authorization': f"Zoho-enczapikey {setting.mail_password}" }
        params = {"from": {"address": setting.mail_from},"to": [{"email_address": {"address": toAddress,"name": toAddress}}],"subject": subject,"htmlbody": body}
        url = setting.mail_server
        if templatekey and template_data:
            url = f"{setting.mail_server}/template"
            params = {"from": {"address": setting.mail_from},"to": [{"email_address": {"address": toAddress,"name": toAddress}}],"subject": subject,
        "template_key": templatekey
        ,"merge_info": template_data}
        res = http(url=url,method='POST',headers=headers,params=params)
    except Exception as e:
        logger.error(f"Error sending email at {datetime.now()} {str(e)}")
        pass
def mailer(body, setting: Setting, subject: str, toAddress: str, fileToSend=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = setting.mail_from
        msg["To"] = toAddress
        msg["Subject"] = subject
        msg.preamble = subject
        msg.attach(MIMEText(body, "html"))

        if fileToSend:
            ctype, encoding = mimetypes.guess_type(fileToSend)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)

            with open(fileToSend, "rb" if maintype != "text" else "r") as fp:
                if maintype == "text":
                    attachment = MIMEText(fp.read(), _subtype=subtype)
                elif maintype == "image":
                    attachment = MIMEImage(fp.read(), _subtype=subtype)
                elif maintype == "audio":
                    attachment = MIMEAudio(fp.read(), _subtype=subtype)
                else:
                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(fp.read())
                    encoders.encode_base64(attachment)

            attachment.add_header("Content-Disposition", "attachment", filename=fileToSend)
            msg.attach(attachment)

        logger.info(f"Sending mail to {toAddress} via {setting.mail_server}:{setting.mail_port}")
        server = smtplib.SMTP(setting.mail_server, setting.mail_port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(setting.mail_username, setting.mail_password)
        server.sendmail(setting.mail_from, toAddress, msg.as_string())
        server.quit()

    except Exception as e:
        logger.error(f"Error sending email: {e}")
def send_sms_message(setting: Setting, toPhoneNumber: str, message: str,transactionId:str):
    try:
        logger.info(f"started sending SMS to {toPhoneNumber} with text {message} with transactionId {transactionId}")
        payload ={
            "sms": {
                "dest":toPhoneNumber,
                "referenceId":transactionId,
                "src": setting.senderid,
                "text": message,
                "unicode": True
                },
                "account": {
                    "password":setting.vanso_password,
                    "systemId":setting.vanso_username
                    }
            }
        response = httpV2(url=setting.vanso_url,params=payload)
        if response.status_code == 200:
            return True
        return False
    except Exception as ex:
        logger.error(str(ex))
        pass
def amountToKobo(amount):
    return str(int(float(amount) * 100))
def kobo_to_naira(kobo_amount):
    naira = kobo_amount / 100
    return round(naira, 2)
def formatPhoneWithDialingCode(msisdn):
    msisdn = msisdn.replace("+", "", 1)
    if msisdn.startswith("234") and len(msisdn) == 13:
        return msisdn
    elif msisdn.startswith("0") and len(msisdn) == 11:
        return msisdn.replace("0", "234", 1)
    elif len(msisdn) == 10:
        return f"234{msisdn}"
    else:
        return msisdn
def formatPhone(msisdn:str)->str:
    msisdn = msisdn.replace("+", "", 1)
    if msisdn.startswith("234") and len(msisdn) == 13:
        return msisdn.replace("234", "0", 1)
    elif not msisdn.startswith("0") and len(msisdn) == 10:
        return f"0{msisdn}"
    elif msisdn.startswith("0") and len(msisdn) == 11:
        return msisdn
    else:
        return msisdn
def formatPhoneShort(msisdn:str)->str:
    msisdn = msisdn.replace("+", "", 1)
    if msisdn.startswith("234") and len(msisdn) == 13:
        return msisdn.replace("234", "", 1)  #
    elif msisdn.startswith("0") and len(msisdn) == 11:
        return msisdn.replace("0", "", 1)
    else:
        return msisdn
def mask_emailold(email):
    return re.sub(r'^[^@]+', '*' * len(re.search(r'^[^@]+', email).group()), email)
def mask_email(email: str) -> str:
    match = re.search(r'^[^@]+', email)
    if not match:
        return email  # no username part
    username = match.group()
    if len(username) <= 2:
        return email  # nothing to mask
    masked = username[:2] + '*' * (len(username) - 2)
    return re.sub(r'^[^@]+', masked, email)
def generateId(length: int = 12) -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(length))
def sanitize_input(text: str) -> str:
    return re.sub(r'[^\w-]', '', text)
def generateOTP():
    return str(randint(100000, 999999))
def generateBillerId():
    return str(randint(1000, 9999))
def find_item(items, key, value):
    return next((x for x in items if x.billerId == value), None)
def generateUniqueId():
    return "2510" + str(uuid.uuid5(uuid.NAMESPACE_DNS, "smarttap.org").int)
def formatDateOfBirth(dob:str):
    try:
        input_date = datetime.strptime(dob, "%d-%b-%y")
        return input_date.strftime("%d%m%Y")
    except Exception as ex:
        return None
def formatDateOfBirthForOpenAcct(dob:str)->Union[str,None]:
    try:
        input_date = datetime.strptime(dob,"%d%m%Y")
        return input_date.strftime("%Y-%m-%d")
    except Exception as ex:
        return None
def parseVerifymeDateOfBirth(dob:str)->Union[str,None]:
    try:
        input_date = datetime.strptime(dob,"%d-%m-%Y")
        return input_date.strftime("%Y%m%d")
    except Exception as ex:
        return None
def generateCheckDigit(serialNumber:str, bankCode:str):
    seed = "373373373373"
    serialNumLength = 9
    #return len(serialNumber) > serialNumLength
    serialNumber = f"{serialNumber:0{serialNumLength}}"
    cipher = bankCode + serialNumber
    sum = 0
    #Step 1. Calculate A*3+B*7+C*3+D*3+E*7+F*3+G*3+H*7+I*3+J*3+K*7+L*3
    for idx, x in enumerate(cipher):
        logger.info(f"{seed[idx]} and {x}")
        sum += int(x) * int(seed[idx])
    #Step 2: Calculate Modulo 10 of your result i.e. the remainder after dividing by 10
    sum %= 10
    #Step 3. Subtract your result from 10 to get the Check Digit
    checkDigit = 10 - sum
    #Step 4. If your result is 10, then use 0 as your check digit
    return 0 if checkDigit == 10 else checkDigit
def formXml(setting: Setting, phone: str, content: str):
    root = ET.Element("operation", {"type": "submit"})
    account = ET.SubElement(
        root,
        "account",
        {"username": setting.vanso_username, "password": setting.vanso_password},
    )
    submitRequest = ET.SubElement(root, "submitRequest")
    deliveryReport = ET.SubElement(submitRequest, "deliveryReport")
    deliveryReport.text = "true"
    sourceAddress = ET.SubElement(submitRequest, "sourceAddress", {"type": "network"})
    sourceAddress.text = setting.senderid
    destinationAddress = ET.SubElement(
        submitRequest, "destinationAddress", {"type": "international"}
    )
    destinationAddress.text = f"+{formatPhone(phone)}"
    text = ET.SubElement(submitRequest, "text", {"encoding": "ISO-8859-1"})
    text.text = stringToHex(content)
    xml = ET.tostring(root, xml_declaration=True, encoding="iso-8859-1")
    logger.info(xml)
    return xml
def stringToHex(string):
    st = ""
    for char in string:
        d = bytearray(char, "ISO-8859-1")
        st = st + hex(ord(d))[2:]
    logger.info(st)
    return st
def create_access_token(setting: Setting, credentials: dict, exp:Union[int,None]=20):
    encoded_credentials = credentials.copy()

    expire = datetime.now() + timedelta(
        hours=setting.access_token_expire_minutes
    )
    if exp:
        expire = datetime.now() + timedelta(minutes=exp)
    encoded_credentials.update({"exp": expire})
    encoded_jwt = jwt.encode(
        encoded_credentials, setting.secret_key, algorithm=setting.algorithm
    )
    return [encoded_jwt,str(exp*60)]
# Hash a password using bcrypt
def get_password_hash(password):
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password
# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password, hashed_password):
    logger.info(plain_password)
    logger.info(hashed_password.encode("utf-8"))
    password_byte_enc = plain_password.encode("utf-8")
    return bcrypt.checkpw(
        password=password_byte_enc, hashed_password=hashed_password.encode("utf-8")
    )
def convert_thousand_separator_to_str(number_str):
    # Set the locale to the user's default locale
    locale.setlocale(locale.LC_ALL, '')

    # Convert the string to a float
    number = float(locale.atof(number_str))

    # Convert the float back to a string with the thousand separator
    return locale.format_string("%d", number, grouping=True)
def getKoboValue(amount:str):
    amount = amount.replace(',', '')
    kobo = int(float(amount) * 100)
    return kobo
def decodeId(id:str):
    decoded_bytes = base64.b64decode(id)
    return decoded_bytes.decode('utf-8')
def get_first_day_of_month():
    today = datetime.today()
    return datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
def get_today():
    return datetime.today().strftime("%Y-%m-%d")
def get_lat_lon(location_name: str):
    logger.info(f"getting geolocation info for ${location_name} at {datetime.now()}")
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    return None, None
def is_within_radius(lat1, lon1, lat2, lon2, radius_km):
    logger.info(f"Started calculation............ {lat1,lat2} and {lon1,lon2}")
    R = 6371.0  # Earth radius in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # distance in km
    logger.info(f"distance {distance} and radius {radius_km}")
    return distance <= radius_km
PASSWORD_REGEX = re.compile(
    r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^\w\s]).{8,}$'
)
def validate_strong_password(v: str) -> str:
    if len(v) < 10:
        raise ValueError("Password must be at least 10 characters")
    if any(ch.isspace() for ch in v):
        raise ValueError("Password cannot contain spaces")
    if not any(ch.isupper() for ch in v):
        raise ValueError("Password must contain at least one uppercase")
    if not any(ch.islower() for ch in v):
        raise ValueError("Password must contain at least one lowercase")
    if not any(ch.isdigit() for ch in v):
        raise ValueError("Password must contain at least one digit")
    if not any(ch in "!@#$%^&*()_-+=" for ch in v):
        raise ValueError("Password must contain at least one special character")
    return v
@lru_cache()
def get_setting():
    return AppSetting()
class UnicornException(Exception):
    def __init__(self, status: int, error: dict):
        self.status = status
        self.name = error
