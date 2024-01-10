""" AI model """
from typing import Optional
from uuid import UUID
import uuid

from sqlmodel import Field, SQLModel

class AI(SQLModel, table=True):
    """ AI model. """
    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
