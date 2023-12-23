from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel

class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)

class UserRead(UserBase):
    id: UUID

class UserCreate(UserBase):
    password: str

class AuthenticatedUser(UserBase, table=True):
    id: Optional[UUID] = Field(default=None, primary_key=True)
    hashed_password: str