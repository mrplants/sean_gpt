""" Performs the second stage of file processing: calculate vector embedding for chunk

This file is used as a kubernetes job that retrieves a text chunk from a kafka topic, calculates
the vector embedding, and posts the result to milvus.
"""
from typing import Tuple, List
import json
from unittest.mock import patch

from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from openai import OpenAI
from pymilvus import connections, Collection
from sqlalchemy import create_engine, text

from ..util.describe import describe
from ..config import settings
from ..model.file import FILE_STATUS_COMPLETE, TextFileChunkingStatus
from ..util.database import _DATABASE_URL

if settings.debug:
    def get_random_embedding(*args, **kwargs):
        """ Mocks the openai embeddings endpoint.
        """
        print('Mock OpenAI embeddings request:', kwargs['input'])
        if type(kwargs['input']) == str:
            return {
                "object": "list",
                "data": [
                    {
                    "object": "embedding",
                    "embedding": [0.0 for _ in range(1536)],
                    "index": 0
                    }
                ],
                "model": "text-embedding-ada-002",
                "usage": {
                    "prompt_tokens": 8,
                    "total_tokens": 8
                }
            }
        else:
            # The input is a list of strings
            # So return a list of embeddings that matches the length of the input
            return {
                "object": "list",
                "data": [
                    {
                    "object": "embedding",
                    "embedding": [0.0 for _ in range(1536)],
                    "index": i
                    } for i in range(len(kwargs['input']))
                ],
                "model": "text-embedding-ada-002",
                "usage": {
                    "prompt_tokens": 8,
                    "total_tokens": 8
                }
            }
    embeddings_patch = patch('openai.resources.Embeddings.create',
                            new=get_random_embedding)
    embeddings_patch.start()

openai_client = OpenAI(api_key = settings.openai_api_key)
connections.connect(host=settings.milvus_host, port=settings.milvus_port)
milvus_collection = Collection(name=settings.milvus_collection_name)

engine = create_engine(_DATABASE_URL, echo=settings.debug)

CHUNK_BATCH_SIZE = 10

@describe(
""" Retrieves a chunk from a kafka topic
""")
def get_chunks_from_kafka_topic(kafka_topic: str) -> dict|None:
    """ Retrieves a chunk from a kafka topic
    """
    # Retrieve a single file ID from the stage 1 kafka topic
    message_consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=settings.kafka_brokers,
        group_id=kafka_topic,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    records = message_consumer.poll(max_records=CHUNK_BATCH_SIZE, timeout_ms=5000, update_offsets=True)
    if not records:
        message_consumer.close()
        return None
    # The first record in the first partition
    chunk_dicts = [msg.value for msg in records[TopicPartition(topic=kafka_topic, partition=0)]]
    message_consumer.commit()
    message_consumer.close()
    return chunk_dicts

@describe(
""" Calculates the vector embedding for a chunk of text
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
""" Posts the vector embedding to milvus
""")
def post_vector_embedding_to_milvus(chunk_embeddings: List[List[float]], chunk_dicts: List[dict]):
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
            raise Exception(f"File with ID {file_id} not found in database.")

        return result[0], result[1]

if __name__ == '__main__':
    # Retrieve a chunk from the kafka topic
    # TODO: Make this work on a batch of chunks for efficiency
    chunks = get_chunks_from_kafka_topic('file_processing_stage_1')
    if not chunks:
        print('No chunks retrieved from kafka topic.')
        exit()
    # Calculate the vector embedding
    vector_embeddings = calculate_vector_embedding([chunk_dict['chunk_txt'] for chunk_dict in chunks])
    # Post the vector embedding to milvus
    post_vector_embedding_to_milvus(vector_embeddings, chunks)
    # debug
    # Increment the count of chunk's processed in postgres
    for chunk_dict in chunks:
        file_id = chunk_dict['file_id']
        chunks_processed, total_chunks = increment_chunks_processed_count(file_id)
        # debug
        # If the count of chunks processed is equal to the total number of chunks, post to the
        # status topic that the file is processed
        if chunks_processed == total_chunks:
            # Make a kafka producer
            producer = KafkaProducer(
                bootstrap_servers=settings.kafka_brokers,
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            producer.send(
                'monitor_file_processing',
                key=str(file_id),
                value={
                    'status': FILE_STATUS_COMPLETE
                }
            )
            producer.flush()
            producer.close()
