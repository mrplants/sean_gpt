""" Performs the first stage of file processing: chunking

This file is used as a kubernetes job that retrieves a file ID from a queue, downloads the
file from minio, and then chunks the file, posting the chunks to aqueye for processing by
stage 1.
"""
import os
import tempfile
import json
import uuid

from typing import Generator
import asyncio

from sqlmodel import Session, select
import aio_pika

from ..util.describe import describe
from ..model.file import File, FILE_STATUS_PROCESSING, TextFileChunkingStatus
from ..config import settings
from ..util.minio_client import get_minio_client, USER_UPLOAD_BUCKET_NAME
from ..util.database import get_db_engine

CHUNK_LENGTH = 500
CHUNK_STRIDE = 100

import asyncio
import json
from typing import Generator
import aio_pika

async def get_file_id_from_queue(name: str) -> Generator[str, None, None]:
    """Retrieves file IDs from the queue.

    This function connects to a RabbitMQ queue and retrieves file IDs. If no message
    is received within 5 seconds, the loop breaks and stops listening for new messages.

    Args:
        name (str): The name of the queue to connect to.

    Yields:
        Generator[str, None, None]: A generator yielding file IDs.
    """
    connection = await aio_pika.connect_robust(host=settings.rabbitmq_host,
                                               login=settings.rabbitmq_secret_username,
                                               password=settings.rabbitmq_secret_password)

    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Declaring queue
        queue = await channel.declare_queue(name)

        async with queue.iterator() as queue_iter:
            while True:
                try:
                    # Wait for a message for 5 seconds, then break if timeout occurs
                    message = await asyncio.wait_for(queue_iter.__anext__(), timeout=5)
                except asyncio.TimeoutError:
                    # Break the loop if no message is received in 5 seconds
                    print("No message received in 5 seconds. Exiting.", flush=True)
                    break
                else:
                    async with message.process():
                        payload = json.loads(message.body.decode('utf-8'))
                        yield payload['file_id']

@describe(
""" Downloads a file from minio, and returns the temporary file path.
""")
def download_file_from_minio(file_id: str) -> str:
    """ Downloads a file from minio, and returns the temporary file path.
    """
    # Download the file from minio
    # Create a Minio client
    # Retrieve the file from minio, directly to a temporary file
    print(f"Downloading file {file_id} from minio", flush=True)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        get_minio_client().fget_object(
            USER_UPLOAD_BUCKET_NAME,
            file_id,
            temp_file.name
        )
    print(f"File {file_id} downloaded from minio", flush=True)
    return temp_file.name

@describe(
""" Retrieves a file record from postgres.
""")
def get_file_record_from_postgres(file_id: str) -> File|None:
    """ Retrieves a file record from postgres.
    """
    # Retrieve the file record from postgres
    with Session(get_db_engine()) as session:
        file_record = session.exec(select(File).where(File.id == file_id)).first()
        if not file_record:
            print(f"File with ID {file_id} not found in database.", flush=True)
            return None
        return file_record

@describe(
""" Chunks a txt file, and posts the chunks to a kafka topic.
""")
async def chunk_txt_file(file_id: str, temp_file_path: str, file_record: File):
    """ Chunks a txt file, and posts the chunks to a kafka topic.
    """
    # Save the chunks to the local filesystem in temporary files, temporary subdirectory named "chunks"
    # Create a temporary directory for all chunks
    print('creating temporary directory for chunks', flush=True)
    num_chunks = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary file for each chunk
        print('creating temporary files for chunks', flush=True)
        with open(temp_file_path, "r", encoding='utf-8') as file:
            while True:
                file_chunk = file.read(CHUNK_LENGTH)
                if not file_chunk:
                    break
                # Create a temporary file for the chunk with the name as the chunk location
                with open(os.path.join(temp_dir, str(file.tell() - len(file_chunk))), "w", encoding='utf-8') as temp_file:
                    temp_file.write(file_chunk)
                    num_chunks += 1
        # Create a record to track the chunking status
        with Session(get_db_engine()) as session:
            session.add(
                TextFileChunkingStatus(
                    file_id=uuid.UUID(file_id),
                    total_chunks=num_chunks
                )
            )
            session.commit()
        print(f"File {file_id} has {num_chunks} chunks", flush=True)
        # The chunk processing will happen in a separate kubernetes job, so post the chunks to a queue.
        # Iterate over all the chunk files, posting each to a queue
        print('posting chunks to queue', flush=True)
        connection = await aio_pika.connect_robust(host=settings.rabbitmq_host,
                                                login=settings.rabbitmq_secret_username,
                                                password=settings.rabbitmq_secret_password)
        async with connection:
            # Creating a channel
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)

            for chunk_file_name in os.listdir(temp_dir):
                # Post the contents of the chunk file to the queue
                with open(os.path.join(temp_dir, chunk_file_name), "r", encoding='utf-8') as chunk_file:
                    message = aio_pika.Message(
                        json.dumps({
                            'file_id': str(file_id),
                            'chunk_txt': chunk_file.read(),
                            'chunk_location': int(chunk_file_name),
                        }).encode('utf-8'), delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    )
                    print(f'Posting chunk: {chunk_file_name}', flush=True)
                    await channel.declare_queue(settings.app_file_processing_stage_chunk2embedding_topic_name)
                    # Sending the message
                    await channel.default_exchange.publish(
                        message, routing_key=settings.app_file_processing_stage_chunk2embedding_topic_name,
                    )

@describe(
""" Chunk a file.
""")
async def chunk_file(file_id: str, file_record: File, temp_file_path: str):
    """ Chunk a file.
    """
    # Chunk the file
    if file_record.type == "txt":
        await chunk_txt_file(file_id, temp_file_path, file_record)
    else:
        print(f"Unsupported file type: {file_record.type}", flush=True)
        return

async def post_file_status(file_id: str, status: str):
    """ Posts the file status to a queue and updates it in the database.
    """
    # Post the file status to a kafka topic
    with Session(get_db_engine()) as session:
        file_record = session.exec(select(File).where(File.id == file_id)).first()
        if not file_record:
            print(f"File with ID {file_id} not found in database.", flush=True)
            return
        file_record.status = status
        session.add(file_record)
        session.commit()
    connection = await aio_pika.connect_robust(host=settings.rabbitmq_host,
                                            login=settings.rabbitmq_secret_username,
                                            password=settings.rabbitmq_secret_password)
    async with connection:
        exchange_name = "monitor_file_processing"

        channel = await connection.channel()

        exchange = await channel.declare_exchange(name=exchange_name, type="fanout")

        await exchange.publish(
            aio_pika.Message(
            json.dumps({
                'file_id': file_id,
                'status': status
            }).encode('utf-8'),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
            routing_key='',
        )

@describe(
""" Main function.
""")
async def main():
    # Iterate over the queue of file IDs, chunking each file
    print("Starting file processing", flush=True)
    async for file_id in get_file_id_from_queue(settings.app_file_processing_stage_txtfile2chunk_topic_name):
        # Post to the status topic that the file is processing
        print(f"Processing file {file_id}", flush=True)
        print(f"Posting file status: {FILE_STATUS_PROCESSING}", flush=True)
        await post_file_status(file_id, FILE_STATUS_PROCESSING)
        print(f"File status posted: {FILE_STATUS_PROCESSING}", flush=True)
        # Retrieve the file record from postgres
        print(f"Retrieving file record from postgres", flush=True)
        file_record = get_file_record_from_postgres(file_id)
        print(f"File record retrieved from postgres: {file_record}", flush=True)
        if not file_record:
            print(f"File with ID {file_id} not found in database.", flush=True)
            continue
        # Download the file from minio
        print(f"Downloading file {file_id} from minio", flush=True)
        temp_file_path = download_file_from_minio(file_id)
        print(f"File {file_id} downloaded from minio", flush=True)
        # Chunk the file
        print(f"Chunking file {file_id}", flush=True)
        await chunk_file(file_id, file_record, temp_file_path)
        print(f"File {file_id} chunked", flush=True)
        # Delete the temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    asyncio.run(main())
