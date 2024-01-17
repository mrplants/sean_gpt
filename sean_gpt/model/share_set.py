""" ShareSet model.
"""
import uuid
from uuid import UUID

from sqlmodel import Field, SQLModel

class ShareSet(SQLModel, table=True):
    """ ShareSet model. """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    is_public: bool
