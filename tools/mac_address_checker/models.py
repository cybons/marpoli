from pydantic import BaseModel


class MACRequest(BaseModel):
    hostname: str
    mac_address: str
