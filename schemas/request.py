from pydantic import BaseModel

class TransactionPINRequest(BaseModel):
    pin: str