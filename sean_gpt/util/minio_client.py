""" Minio utilities.
"""
from typing import Annotated, Any
import logging

from minio import Minio
from fastapi import Depends

from .describe import describe
from ..config import settings

USER_UPLOAD_BUCKET_NAME = "useruploads"

@describe(
""" FastAPI dependency to get a minio client. """)
def get_minio_client(): # pylint: disable=missing-function-docstring
    # Create a Minio client
    minio_client = Minio(
        f"{settings.minio_host}:{settings.minio_port}",
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=True,
        cert_check=False
    )
    try:
        minio_client.list_buckets()
    except Exception as err:
        logging.critical("Object storage not reachable")
        raise err
    # Make sure the user-uploads bucket exists
    if not minio_client.bucket_exists(USER_UPLOAD_BUCKET_NAME):
        minio_client.make_bucket(USER_UPLOAD_BUCKET_NAME)
    return minio_client

MinioClientDep = Annotated[Any, Depends(get_minio_client)]
