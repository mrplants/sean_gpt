""" File DELETE endpoint.
"""
import uuid
from typing import Annotated, List, Union

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ...util.database import SessionDep
from ...util.describe import describe
from ...model.file import File, ShareSet, FileShareSetLink

router = APIRouter(
    prefix="/file"
)

@describe(
""" Gets a file.

Args:
    file_id (UUID): The id of the file to retrieve.
    share_set_id (UUID): The id of the share set to retrieve.
    semantic_content_query (str): The semantic content query to match.
    session (SessionDep): The database session.
""")
@router.get("")
async def get_files( # pylint: disable=missing-function-docstring
    *,
    file_id: Annotated[Union[uuid.UUID, None], Query()] = None,
    share_set_id: Annotated[uuid.UUID | None, Query()] = None,
    semantic_content_query: Annotated[str | None, Query()] = None,
    session: SessionDep) -> List[File]:
    # Retrieve the file by file_id
    # Can only use file_id if share_set_id  and semantic_content_query are None
    if file_id is not None:
        if share_set_id is not None or semantic_content_query is not None:
            raise HTTPException(status_code=400, detail="Cannot use file_id with other arguments.")
        return session.exec(select(File).where(File.id == file_id)).all()
    # Retrieve a list of files by share_set_id
    # This requires a join with FileShareSetLink
    if share_set_id is not None and semantic_content_query is None:
        return session.exec(
            select(File).join(FileShareSetLink).where(FileShareSetLink.share_set_id == share_set_id)
        ).all()
    # Retrieve a list of files by semantic_content_query
    # TODO: Implement semantic_content_query
        
