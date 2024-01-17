""" File POST endpoint.
"""
import hashlib
import tempfile
import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from ...util.database import SessionDep
from ...util.minio_client import MinioClientDep, USER_UPLOAD_BUCKET_NAME
from ...util.describe import describe
from ...model.file import (
    File as FileModel,
    FILE_STATUS_AWAITING_PROCESSING,
    SUPPORTED_FILE_TYPES,
    ShareSet,
    FileShareSetLink
)

router = APIRouter(
    prefix="/file"
)

@describe(
""" Uploads a file.

Args:
    files (List[UploadFile]): The files to upload.
""")
@router.post("")
async def upload_file( # pylint: disable=missing-function-docstring
    *,
    file: UploadFile = File(...),
    session: SessionDep,
    minio_client: MinioClientDep) -> FileModel:
    # Create the default share set for this file
    default_share_set = ShareSet(name="", is_public=False)
    session.add(default_share_set)
    session.commit()
    session.refresh(default_share_set)
    # Create the file's unique id
    file_id = uuid.uuid4()
    # Hash the file, calculate its size, and put it in temporary storage
    sha256_hash = hashlib.sha256()
    # file_size = 0
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    chunk_size = 8192
    chunk = await file.read(chunk_size)
    while len(chunk) > 0:
        sha256_hash.update(chunk)
        # file_size += len(chunk)
        temp_file.write(chunk)
        chunk = await file.read(chunk_size)
    file_hash = sha256_hash.hexdigest()
    temp_file.close()
    # Store the file in the minio service
    try:
        minio_client.fput_object(
            USER_UPLOAD_BUCKET_NAME,
            str(file_id),
            temp_file.name
        )
    finally:
        # Remove the temporary file
        os.unlink(temp_file.name)
    # Determine the file type from the file extension
    file_extension = os.path.splitext(file.filename)[1][1:]
    if file_extension not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"File type {file_extension} is not supported."
        )
    # Create a file record in the database
    file_record = FileModel(
        id=file_id,
        default_share_set_id=default_share_set.id,
        status=FILE_STATUS_AWAITING_PROCESSING,
        name=file.filename,
        type=file_extension,
        hash=file_hash,
        size=file.size
    )
    session.add(file_record)
    session.commit()
    # Create the link between the file and its default share set
    file_share_set_link = FileShareSetLink(
        file_id=file_id,
        share_set_id=default_share_set.id
    )
    session.add(file_share_set_link)
    session.commit()
    session.refresh(file_record)
    # Return the file record
    return file_record
