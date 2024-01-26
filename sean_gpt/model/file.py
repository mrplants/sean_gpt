""" File model.
"""
import uuid
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel, Relationship

FILE_STATUS_AWAITING_PROCESSING = "awaiting processing"
FILE_STATUS_PROCESSING = "processing"
FILE_STATUS_COMPLETE = "complete"

ORDERED_FILE_STATUSES = (
    FILE_STATUS_AWAITING_PROCESSING,
    FILE_STATUS_PROCESSING,
    FILE_STATUS_COMPLETE,
)

SUPPORTED_FILE_TYPES = (
    # Plaintext file types
    "txt",
)

class TextFileChunkingStatus(SQLModel, table=True):
    """ TextFileStatus model. """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    file_id: UUID = Field(foreign_key="file.id", index=True)
    total_chunks: int
    chunks_processed: int = 0

    file: "File" = Relationship(back_populates="processing_status")

class File(SQLModel, table=True):
    """ File model. """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="authenticateduser.id", index=True)
    default_share_set_id: UUID = Field(foreign_key="shareset.id", index=True)
    status: str
    name: str
    type: str
    hash: str
    uploaded_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()), index=True)
    size: int

    owner: "AuthenticatedUser" = Relationship(back_populates="files")
    file_share_set_links: List["FileShareSetLink"] = Relationship(
        back_populates="file",
        sa_relationship_kwargs={"cascade": "all, delete"})
    
    processing_status: Optional[TextFileChunkingStatus] = Relationship(
        back_populates="file",
        sa_relationship_kwargs={"cascade": "all, delete"})

class ShareSet(SQLModel, table=True):
    """ ShareSet model. """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="authenticateduser.id", index=True)
    name: str
    is_public: bool = False

    owner: "AuthenticatedUser" = Relationship(back_populates="share_sets")
    file_share_set_links: List["FileShareSetLink"] = Relationship(
        back_populates="share_set",
        sa_relationship_kwargs={"cascade": "all, delete"})

class FileShareSetLink(SQLModel, table=True):
    """ FileShareSetLink model. """
    file_id: UUID = Field(
        default=None, foreign_key="file.id", primary_key=True
    )
    share_set_id: UUID = Field(
        default=None, foreign_key="shareset.id", primary_key=True
    )

    file: File = Relationship(back_populates="file_share_set_links")
    share_set: ShareSet = Relationship(back_populates="file_share_set_links")
