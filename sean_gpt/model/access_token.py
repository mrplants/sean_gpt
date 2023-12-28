from pydantic import BaseModel

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class AccessTokenData(BaseModel):
    username: str | None = None