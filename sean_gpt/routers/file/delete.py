""" File DELETE endpoint.
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from pymilvus import connections, Collection

from ...util.user import AuthenticatedUserDep
from ...util.database import SessionDep
from ...util.minio_client import MinioClientDep, USER_UPLOAD_BUCKET_NAME
from ...util.describe import describe
from ...model.file import File, ShareSet, FileShareSetLink
from ...config import settings

router = APIRouter(
    prefix="/file"
)

@describe(
""" Deletes a file.

Args:
    file_id (UUID): The id of the file to delete.
""")
@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file( # pylint: disable=missing-function-docstring
    *,
    file_id: uuid.UUID,
    session: SessionDep,
    minio_client: MinioClientDep,
    current_user: AuthenticatedUserDep) -> None:
    # Delete the file from the database
    file_record = session.exec(select(File).where(File.id == file_id)).first()
    # Only the file owner can delete the file
    if file_record is None or file_record.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete the all the file's share set links from the database
    share_set_links = session.exec(select(FileShareSetLink)
                                   .where(FileShareSetLink.file_id == file_id)).all()
    for share_set_link in share_set_links:
        session.delete(share_set_link)
    # Need to unlink the share sets and files before deleting
    session.commit()

    share_set = session.exec(select(ShareSet).where(ShareSet.id ==
                                                    file_record.default_share_set_id)).first()
    if share_set is None:
        raise HTTPException(status_code=404, detail="Share set not found")
    session.delete(file_record)
    session.commit()

    # Delete the file from the minio service
    try:
        minio_client.remove_object(
            USER_UPLOAD_BUCKET_NAME,
            str(file_id)
        )
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception
    
    # Delete the embeddings associated with this file from milvus
    connections.connect(host=settings.milvus_host, port=settings.milvus_port)
    milvus_collection = Collection(name=settings.milvus_collection_name)
    milvus_collection.load()
    milvus_collection.delete(
        expr='file_id in {}'.format([str(file_id)]),
    )
    
    session.delete(share_set)
    session.commit()
