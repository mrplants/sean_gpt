""" This module contains the AuthenticatedUser model. """
from typing import Optional, List
from uuid import UUID
import uuid

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.sql import text

class UserCreate(SQLModel):
    """ Schema for creating a user. """
    phone: str
    password: str

class UserBase(SQLModel):
    """ Schema for a user. """
    phone: str = Field(index=True, unique=True)
    referral_code: str = Field(
        default_factory=lambda: str(uuid.uuid4()).replace('-', '')[:8].upper(), # pylint: disable=unnecessary-lambda
        index=True,
        unique=True)
    is_phone_verified: bool = Field(default=False)
    opted_into_sms: bool = Field(default=False, sa_column_kwargs={"server_default": text("false"),})
    referrer_user_id: str = Field(index=True)

class UserRead(UserBase):
    """ Schema for reading a user. """
    id: UUID
    twilio_chat_id: str

class AuthenticatedUser(UserBase, table=True):
    """ Authenticated user model. """
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    twilio_chat_id: Optional[str] = None
    hashed_password: str

    verification_token: Optional["VerificationToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete"})
    chats: List["Chat"] = Relationship(back_populates="user",
                                       sa_relationship_kwargs={"cascade": "all, delete"})
    