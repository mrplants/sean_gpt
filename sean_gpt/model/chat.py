from typing import Optional, List
import uuid
from uuid import UUID

from sqlmodel import Field, SQLModel, Relationship

class ChatCreate(SQLModel):
    name: str = Field(default="")

class ChatBase(ChatCreate):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="authenticateduser.id", index=True)
    assistant_id: UUID = Field(foreign_key="ai.id", index=True)
    is_assistant_responding: bool = Field(default=False)

class Chat(ChatBase, table=True):
    user: "AuthenticatedUser" = Relationship(back_populates="chats")

    messages: List["Message"] = Relationship(back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete"})

class ChatRead(ChatBase):
    id: UUID