from typing import Optional
import uuid
from uuid import UUID

from sqlmodel import Field, SQLModel    

class ChatBase(SQLModel):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: Optional[str] = None
    user_id: UUID = Field(foreign_key="authenticateduser.id", index=True)
    assistant_id: UUID = Field(foreign_key="ai.id", index=True)

class Chat(ChatBase, table=True):
    pass

class ChatRead(ChatBase):
    id: UUID