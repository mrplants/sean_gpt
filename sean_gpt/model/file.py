""" File model.
"""
import uuid
from uuid import UUID
from datetime import datetime

from sqlmodel import Field, SQLModel

FILE_STATUS_AWAITING_PROCESSING = "awaiting processing"
FILE_STATUS_PROCESSING = "processing"
FILE_STATUS_COMPLETE = "complete"

SUPPORTED_FILE_TYPES = (
    # Plaintext file types
    "txt",
    "md",
    "rst",

    # Code file types
    "py",
    "c",
    "cpp",
    "h",
    "hpp",
    "java",
    "js",
    "ts",
    "html",
    "css",
    "json",

    # Data file types
    "xml",
    "yaml",
    "yml",
    "csv",
    "tsv",
)

class File(SQLModel, table=True):
    """ File model. """
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    default_share_set_id: UUID = Field(foreign_key="shareset.id", index=True)
    status: str
    name: str
    type: str
    hash: str
    uploaded_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()), index=True)
    size: int
