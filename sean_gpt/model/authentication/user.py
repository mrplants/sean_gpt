from typing import Optional
from uuid import UUID
import uuid

from sqlmodel import Field, SQLModel

class UserBase(SQLModel):
    phone: str = Field(index=True, unique=True)
    referral_code: str = Field(default_factory=lambda: str(uuid.uuid4()).replace('-', '')[:8].upper(), index=True, unique=True)

class UserRead(UserBase):
    id: UUID

class UserCreate(UserBase):
    password: str

class AuthenticatedUser(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str