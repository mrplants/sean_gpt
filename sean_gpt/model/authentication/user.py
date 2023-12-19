from typing import Optional
from odmantic import Model

class User(Model):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: str

class UserDescription(Model):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    