from typing import Optional
from uuid import UUID
import uuid

from sqlmodel import Field, SQLModel, Relationship

class UserCreate(SQLModel):
    phone: str
    password: str

class UserBase(SQLModel):
    phone: str = Field(index=True, unique=True)
    referral_code: str = Field(default_factory=lambda: str(uuid.uuid4()).replace('-', '')[:8].upper(), index=True, unique=True)
    is_phone_verified: bool = Field(default=False)
    referrer_user_id: str = Field(index=True)
    
class UserRead(UserBase):
    id: UUID

class AuthenticatedUser(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

    verification_token: Optional["VerificationToken"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})