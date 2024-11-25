
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import authQuery
from datetime import datetime,timedelta
from schemas import otp
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.admin import Admin
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)