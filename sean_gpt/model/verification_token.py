from typing import Optional
from uuid import UUID
import uuid
import secrets

from sqlmodel import Field, SQLModel, Relationship

from ..config import settings
from .authenticated_user import AuthenticatedUser

class VerificationTokenBase(SQLModel):
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(6), index=True, unique=True)
    expiration: int = Field(default_factory=lambda: int(datetime.now().timestamp()) + settings.verification_token_expire_minutes)
    user_id: UUID = Field(foreign_key="user.id")

class UserRead(VerificationTokenBase):
    id: UUID

class VerificationToken(VerificationTokenBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
