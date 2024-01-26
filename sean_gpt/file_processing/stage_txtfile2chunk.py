""" Performs the first stage of file processing: chunking

This file is used as a kubernetes job that retrieves a file ID from a queue, downloads the
file from minio, and then chunks the file, posting the chunks to aqueye for processing by
stage 1.
"""
import os
import tempfile
import json
import uuid
import sys
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
                    print("No message received in 5 seconds. Exiting.")
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
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        get_minio_client().fget_object(
            USER_UPLOAD_BUCKET_NAME,
            file_id,
            temp_file.name
        )
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
            print(f"File with ID {file_id} not found in database.")
            return None
        return file_record

@describe(
""" Chunks a txt file, and posts the chunks to a kafka topic.
""")
async def chunk_txt_file(file_id: str, temp_file_path: str, file_record: File):
    """ Chunks a txt file, and posts the chunks to a kafka topic.
    """
    # Count the chunks in the file WITHOUT posting them to kafka
    num_chunks = 0
    with open(temp_file_path, "r", encoding='utf-8') as file:
        while True:
            file_chunk = file.read(CHUNK_LENGTH)
            if not file_chunk:
                break
            num_chunks += 1
            seek_position = file.tell() - (CHUNK_LENGTH - CHUNK_STRIDE)
            if seek_position < 0:
                file.seek(0, os.SEEK_END)
            else:
                file.seek(seek_position)
    # Create a record to track the chunking status
    with Session(get_db_engine()) as session:
        session.add(
            TextFileChunkingStatus(
                file_id=uuid.UUID(file_id),
                total_chunks=num_chunks
            )
        )
        session.commit()
    # The chunk processing will happen in a separate kubernetes job, so post the chunks to a queue.
    # Chunk the file
    connection = await aio_pika.connect_robust(host=settings.rabbitmq_host,
                                            login=settings.rabbitmq_secret_username,
                                            password=settings.rabbitmq_secret_password)
    async with connection:
        # Creating a channel
        channel = await connection.channel()

        with open(temp_file_path, "r", encoding='utf-8') as file:
            while True:
                file_chunk = file.read(CHUNK_LENGTH)
                if not file_chunk:
                    break
                # Process the chunk
                print(f"Chunking file {file_id} chunk {file.tell() // CHUNK_LENGTH} of {num_chunks}")
                print(f"Chunk: {file_chunk}")
                message = aio_pika.Message(
                    json.dumps({
                        'file_id': str(file_id),
                        'chunk_txt': file_chunk,
                        'chunk_location': file.tell() - len(file_chunk),
                    }).encode('utf-8'), delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                )

                await channel.declare_queue(settings.app_file_processing_stage_chunk2embedding_topic_name)
                # Sending the message
                await channel.default_exchange.publish(
                    message, routing_key=settings.app_file_processing_stage_chunk2embedding_topic_name,
                )

                seek_position = file.tell() - (CHUNK_LENGTH - CHUNK_STRIDE)
                if seek_position < 0:
                    file.seek(0, os.SEEK_END)
                else:
                    file.seek(seek_position)

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
        print(f"Unsupported file type: {file_record.type}")
        return

async def post_file_status(file_id: str, status: str):
    """ Posts the file status to a queue and updates it in the database.
    """
    # Post the file status to a kafka topic
    with Session(get_db_engine()) as session:
        file_record = session.exec(select(File).where(File.id == file_id)).first()
        if not file_record:
            print(f"File with ID {file_id} not found in database.")
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
    async for file_id in get_file_id_from_queue(settings.app_file_processing_stage_txtfile2chunk_topic_name):
        # Post to the status topic that the file is processing
        await post_file_status(file_id, FILE_STATUS_PROCESSING)
        # Retrieve the file record from postgres
        file_record = get_file_record_from_postgres(file_id)
        if not file_record:
            print(f"File with ID {file_id} not found in database.")
            continue
        # Download the file from minio
        temp_file_path = download_file_from_minio(file_id)
        # Chunk the file
        await chunk_file(file_id, file_record, temp_file_path)
        # Delete the temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    asyncio.run(main())
