from typing import Optional
from uuid import UUID
import uuid
import secrets
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from ..config import settings

class VerificationTokenBase(SQLModel):
    token_hash: str = Field(index=True, unique=True)
    expiration: int = Field(default_factory=lambda: int(datetime.now().timestamp()) + settings.verification_token_expire_minutes)
    user_id: UUID = Field(foreign_key="authenticateduser.id")

class VerificationTokenRead(VerificationTokenBase):
    id: UUID

class VerificationToken(VerificationTokenBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

    user: "AuthenticatedUser" = Relationship(back_populates="verification_token")