from typing import Optional

from sqlmodel import Field, SQLModel

class User(SQLModel):
    email: str

class UserData(User, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str