import uuid
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlmodel import Field, SQLModel, Relationship

class RoleType(str, Enum):
    # The only valid roles are "user" and "assistant".
    user = "user"
    assistant = "assistant"

class MessageCreate(SQLModel):
    role: RoleType
    content: str

class MessageBase(MessageCreate):
    chat_index: int = 0
    chat_id: UUID = Field(foreign_key="chat.id", index=True)
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()), index=True)

class Message(MessageBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

    chat: "Chat" = Relationship(back_populates="messages")

class MessageRead(MessageBase):
    id: UUID