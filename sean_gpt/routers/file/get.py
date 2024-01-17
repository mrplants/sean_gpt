""" File DELETE endpoint.
"""
import uuid
from typing import Annotated, List, Union
import tempfile
import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlmodel import select

from ...util.minio_client import MinioClientDep, USER_UPLOAD_BUCKET_NAME
from ...util.database import SessionDep
from ...util.user import AuthenticatedUserDep
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
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> List[File]:
    # Important:  A file can only be accessed if it is:
    #   1. Owned by the user making the request OR
    #   2. A public file
    # A file is public if the default share set is public
    ret_files = []
    # Retrieve the file by file_id
    # Can only use file_id if share_set_id  and semantic_content_query are None
    if file_id is not None:
        if share_set_id is not None or semantic_content_query is not None:
            raise HTTPException(status_code=400, detail="Cannot use file_id with other arguments.")

        ret_files = session.exec(select(File).where(File.id == file_id)).all()
    # Retrieve a list of files by share_set_id
    # This requires a join with FileShareSetLink
    elif share_set_id is not None and semantic_content_query is None:
        return session.exec(
            select(File).join(FileShareSetLink).where(FileShareSetLink.share_set_id == share_set_id)
        ).all()
    # Retrieve a list of files by semantic_content_query
    elif semantic_content_query is not None:
        # TODO: Implement semantic_content_query
        raise HTTPException(status_code=501, detail="semantic_content_query not implemented.")
    else:
        raise HTTPException(status_code=400, detail="Must specify file_id, share_set_id, or "
                                                    "semantic_content_query.")

    # Filter out files that cannot be accessed by the user
    file_ids_to_keep = []
    for file in ret_files:
        # Check if the user owns the file
        if file.owner_id == current_user.id:
            file_ids_to_keep.append(file.id)
            continue
        # Check if the file is public
        default_share_set = session.exec(select(ShareSet).where(ShareSet.id ==
                                                                file.default_share_set_id)).first()
        if default_share_set.is_public:
            file_ids_to_keep.append(file.id)
            continue

    # Filter out files that cannot be accessed by the user
    ret_files = [file for file in ret_files if file.id in file_ids_to_keep]
    return ret_files

@describe(
""" Downloads a file.

Args:
    id (UUID): The id of the file to download.

Returns:
    FileResponse: The file to download.
""")
@router.get("/download/{file_id}")
async def download_file( # pylint: disable=missing-function-docstring
    file_id: uuid.UUID,
    session: SessionDep,
    minio_client: MinioClientDep,
    current_user: AuthenticatedUserDep) -> FileResponse:
    # Important:  A file can only be downloaded if it is:
    #   1. Owned by the user making the request OR
    #   2. A public file
    # A file is public if the default share set is public
    file = session.exec(select(File).where(File.id == file_id)).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found.")
    # Check if the user can access the file
    if file.owner_id != current_user.id:
        # Check if the file is public
        default_share_set = session.exec(select(ShareSet).where(ShareSet.id ==
                                                                file.default_share_set_id)).first()
        if not default_share_set.is_public:
            raise HTTPException(status_code=404, detail="File not found.")
    
    # Retrieve the file from minio, directly to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        minio_client.fget_object(
            USER_UPLOAD_BUCKET_NAME,
            str(file.id),
            temp_file.name
        )
    
    async def delete_temp_file():
        """ Deletes the temporary file. """
        os.unlink(temp_file.name)

    # Return the file
    return FileResponse(temp_file.name,
                        filename=file.name,
                        background=delete_temp_file)
