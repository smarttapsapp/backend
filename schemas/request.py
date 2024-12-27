from pydantic import BaseModel

class PINRequest(BaseModel):
    pin: str