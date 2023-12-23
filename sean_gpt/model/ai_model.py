from sqlmodel import Field, SQLModel
from typing import Optional
from uuid import UUID
import uuid

class AI(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
