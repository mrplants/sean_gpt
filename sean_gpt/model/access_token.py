""" Access Token Model """
from pydantic import BaseModel

class AccessToken(BaseModel):
    """ Access Token Model """
    access_token: str
    token_type: str

class AccessTokenData(BaseModel):
    """ Access Token Data Model """
    username: str | None = None
