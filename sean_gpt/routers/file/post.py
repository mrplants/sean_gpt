""" File POST endpoint.
"""
import hashlib
import tempfile
import os
import uuid
import json

from fastapi import APIRouter, UploadFile, File, HTTPException
import aio_pika

from ...util.user import AuthenticatedUserDep
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
from ...config import settings

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
    minio_client: MinioClientDep,
    current_user: AuthenticatedUserDep) -> FileModel:
    # Determine the file type from the file extension
    file_extension = os.path.splitext(file.filename)[1][1:]
    if file_extension not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"File type {file_extension} is not supported."
        )
    # Create the default share set for this file
    default_share_set = ShareSet(name="",
                                 is_public=False,
                                 owner_id=current_user.id)
    session.add(default_share_set)
    session.commit()
    session.refresh(default_share_set)
    # Create the file's unique id
    file_id = uuid.uuid4()
    # Hash the file, calculate its size, and put it in temporary storage
    sha256_hash = hashlib.sha256()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    chunk_size = 8192
    chunk = await file.read(chunk_size)
    while len(chunk) > 0:
        sha256_hash.update(chunk)
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
    # Create a file record in the database
    file_record = FileModel(
        id=file_id,
        owner_id=current_user.id,
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
    # Pass the file's status (awaiting processing) to the queue for file-monitoring
    connection = await aio_pika.connect_robust(host=settings.rabbitmq_host,
                                            login=settings.rabbitmq_secret_username,
                                            password=settings.rabbitmq_secret_password)
    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange(name="monitor_file_processing", type="fanout")

        await exchange.publish(
            aio_pika.Message(
            json.dumps({
                'file_id': str(file_id),
                'status': FILE_STATUS_AWAITING_PROCESSING
            }).encode('utf-8'),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
            routing_key='',
        )

        await channel.declare_queue(settings.app_file_processing_stage_txtfile2chunk_topic_name)
        # Sending the message
        await channel.default_exchange.publish(
            aio_pika.Message(
            json.dumps({
                'file_id': str(file_id),
            }).encode('utf-8'), delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ), routing_key=settings.app_file_processing_stage_txtfile2chunk_topic_name,
        )

    # Return the file record
    return file_record
