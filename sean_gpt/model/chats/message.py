import uuid
from uuid import UUID
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship

from .chat import Chat

class MessageCreate(SQLModel):
    role: str = "user"
    content: str

class MessageBase(MessageCreate):
    chat_index: int = 0
    chat_id: UUID = Field(foreign_key="chat.id", index=True)
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()), index=True)

class Message(MessageBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

class MessageRead(MessageBase):
    id: UUID