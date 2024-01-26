""" Performs the second stage of file processing: calculate vector embedding for chunk

This file is used as a kubernetes job that retrieves a text chunk from a kafka topic, calculates
the vector embedding, and posts the result to milvus.
"""
from typing import Tuple, List, Generator
import json
import asyncio

from openai import OpenAI
from pymilvus import connections, Collection
from sqlalchemy import create_engine, text
import aio_pika

from ..util.describe import describe
from ..config import settings
from ..model.file import FILE_STATUS_COMPLETE, TextFileChunkingStatus
from ..util.database import _DATABASE_URL

if settings.debug:
    from ..routers.mock.openai import startup
    startup()

openai_client = OpenAI(api_key = settings.openai_api_key)
connections.connect(host=settings.milvus_host, port=settings.milvus_port)
milvus_collection = Collection(name=settings.milvus_collection_name)

engine = create_engine(_DATABASE_URL, echo=settings.debug)

CHUNK_BATCH_SIZE = 10

async def get_chunk_from_queue(name: str) -> Generator[str, None, None]:
    """Retrieves chunks from the queue.

    This function connects to a RabbitMQ queue and retrieves chunks. If no message
    is received within 5 seconds, the loop breaks and stops listening for new messages.

    Args:
        name (str): The name of the queue to connect to.

    Yields:
        Generator[str, None, None]: A generator yielding chunks.
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
                    yield None
                    break
                else:
                    async with message.process():
                        payload = json.loads(message.body.decode('utf-8'))
                        yield payload

@describe(
""" Calculates the vector embedding for chunks of text
""")
def calculate_vector_embedding(chunks: List[str]) -> List[List[float]]:
    """ Calculates the vector embedding for a chunk of text
    """
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=chunks,
        encoding_format="float"
    )
    embeddings = [embedding['embedding'] for embedding in response['data']]
    return embeddings

@describe(
""" Posts the vector embeddings to milvus
""")
def post_vector_embeddings_to_milvus(chunk_embeddings: List[List[float]], chunk_dicts: List[dict]):
    """ Posts the vector embedding to milvus
    """
    for embedding, chunk_dict in zip(chunk_embeddings, chunk_dicts):
        milvus_record = {**chunk_dict, 'chunk_embedding':embedding}
        milvus_collection.insert(milvus_record)
    milvus_collection.flush()

@describe(
""" Increments the count of chunks processed in postgres
""")
def increment_chunks_processed_count(file_id: str) -> Tuple[int, int]:
    """ Increments the count of chunks processed in postgres
    """
    table_name = TextFileChunkingStatus.__tablename__
    with engine.begin() as conn:
        # Atomically increment the chunks_processed count and return the updated record
        result = conn.execute(
            text(
                f"UPDATE {table_name} SET chunks_processed = chunks_processed + 1 "
                f"WHERE file_id = :file_id RETURNING chunks_processed, total_chunks"
            ),
            {"file_id": file_id}
        ).first()

        if not result:
            print(f"File with ID {file_id} not found in database.")
            return None, None

        return result[0], result[1]

async def main():
    """ Main function
    """
    # Begin retrieving chunks one by one from the queue, batching them up
    batch = []
    async for chunk_dict in get_chunk_from_queue(settings.app_file_processing_stage_chunk2embedding_topic_name):
        if chunk_dict:
            batch.append(chunk_dict)
        if len(batch) < CHUNK_BATCH_SIZE and chunk_dict:
            continue
        # Calculate the vector embedding
        vector_embeddings = calculate_vector_embedding([chunk['chunk_txt'] for chunk in batch])
        # Post the vector embedding to milvus
        post_vector_embeddings_to_milvus(vector_embeddings, batch)
        # Increment the count of chunks processed in postgres
        for chunk in batch:
            file_id = chunk['file_id']
            chunks_processed, total_chunks = increment_chunks_processed_count(file_id)
            if not chunks_processed:
                continue
            # If the count of chunks processed is equal to the total number of chunks, post to the
            # status queue that the file is processed
            if chunks_processed == total_chunks:
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
                            'status': FILE_STATUS_COMPLETE
                        }).encode('utf-8'),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                        routing_key='',
                    )

if __name__ == '__main__':
    asyncio.run(main())
