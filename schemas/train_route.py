from typing import Union
from datetime import datetime
from pydantic import BaseModel
from schemas.station import StationBase
from schemas.admin import AdminMini


class TrainRouteBase(BaseModel):
    sourceStation: Union[StationBase, None] = None
    destinationStation: Union[StationBase, None] = None
    identifier: Union[str, None] = None
    provider: Union[AdminMini, None] = None
    class Config:
        from_attributes = True
        populate_by_name = True

class TrainRoute(TrainRouteBase):
    created_at: Union[datetime, None] = datetime.now()
    updated_at: Union[datetime, None] = datetime.now()

    class Config:
        from_attributes = True
        populate_by_name = True