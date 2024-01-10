""" Chat model """
from typing import Optional, List
import uuid
from uuid import UUID

from sqlmodel import Field, SQLModel, Relationship

class ChatCreate(SQLModel):
    """ Schema for creating a chat. """
    name: str = Field(default="")

class ChatBase(ChatCreate):
    """ Schema for a chat. """
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="authenticateduser.id", index=True)
    assistant_id: UUID = Field(foreign_key="ai.id", index=True)
    is_assistant_responding: bool = Field(default=False)

class Chat(ChatBase, table=True):
    """ Chat model. """
    user: "AuthenticatedUser" = Relationship(back_populates="chats")

    messages: List["Message"] = Relationship(back_populates="chat",
                                             sa_relationship_kwargs={"cascade": "all, delete"})

class ChatRead(ChatBase):
    """ Schema for reading a chat. """
    id: UUID
