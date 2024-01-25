""" Performs the first stage of file processing: chunking

This file is used as a kubernetes job that retrieves a file ID from a kafka topic, downloads the
file from minio, and then chunks the file, posting the chunks to a kafka topic for processing by
stage 1.
"""
import os
import tempfile
import json
import uuid
import sys

from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from sqlmodel import Session, select

from ..util.describe import describe
from ..model.file import File, FILE_STATUS_PROCESSING, TextFileChunkingStatus
from ..config import settings
from ..util.minio_client import get_minio_client, USER_UPLOAD_BUCKET_NAME
from ..util.database import get_db_engine

CHUNK_LENGTH = 500
CHUNK_STRIDE = 100

@describe(
""" Retrieves a single file ID from a kafka topic
""")
def get_file_id_from_kafka_topic(kafka_topic: str) -> str:
    """ Retrieves a single file ID from a kafka topic
    """
    # Retrieve a single file ID from the stage 0 kafka topic
    message_consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=settings.kafka_brokers,
        group_id=kafka_topic,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    records = message_consumer.poll(max_records=1, timeout_ms=5000, update_offsets=True)
    if not records:
        message_consumer.close()
        print(f"File ID not found in kafka topic {kafka_topic}.")
        sys.exit(0)
    file_id = records[TopicPartition(topic=kafka_topic, partition=0)][0].value['file_id']
    message_consumer.commit()
    message_consumer.close()
    return file_id

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
def get_file_record_from_postgres(file_id: str) -> File:
    """ Retrieves a file record from postgres.
    """
    # Retrieve the file record from postgres
    with Session(get_db_engine()) as session:
        file_record = session.exec(select(File).where(File.id == file_id)).first()
        if not file_record:
            print(f"File with ID {file_id} not found in database.")
            sys.exit(0)
        return file_record

@describe(
""" Chunks a txt file, and posts the chunks to a kafka topic.
""")
def chunk_txt_file(file_id: str, temp_file_path: str, file_record: File, producer: KafkaProducer):
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
    # The chunk processing will happen in a separate kubernetes job, so post the chunks to a kafka
    # topic.
    # Chunk the file
    with open(temp_file_path, "r", encoding='utf-8') as file:
        while True:
            file_chunk = file.read(CHUNK_LENGTH)
            if not file_chunk:
                break
            # Process the chunk
            # debug
            producer.send(
                'file_processing_stage_1',
                {
                    'file_id': str(file_id),
                    'chunk_txt': file_chunk,
                    'chunk_location': file.tell() - len(file_chunk),
                }
            )
            seek_position = file.tell() - (CHUNK_LENGTH - CHUNK_STRIDE)
            if seek_position < 0:
                file.seek(0, os.SEEK_END)
            else:
                file.seek(seek_position)
    producer.flush()

@describe(
""" Chunk a file.
""")
def chunk_file(file_id: str, file_record: File, temp_file_path: str, next_stage_producer: KafkaProducer):
    """ Chunk a file.
    """
    # Chunk the file
    if file_record.type == "txt":
        chunk_txt_file(file_id, temp_file_path, file_record, next_stage_producer)
    else:
        print(f"Unsupported file type: {file_record.type}")
        sys.exit(0)

if __name__ == "__main__":
    # Retrieve a single file ID from the stage 0 kafka topic
    file_id = get_file_id_from_kafka_topic('file_processing_stage_0')
    if file_id is None:
        exit(0)
    # Make a kafka producer
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_brokers,
        key_serializer=lambda x: x.encode('utf-8') if x else None,
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    # Post to the status topic that the file is processing
    producer.send(
        'monitor_file_processing',
        key=str(file_id),
        value={
            'status': FILE_STATUS_PROCESSING
        }
    )
    producer.flush()
    # Retrieve the file record from postgres
    file_record = get_file_record_from_postgres(file_id)
    # Download the file from minio
    temp_file_path = download_file_from_minio(file_id)
    # Chunk the file
    chunk_file(file_id, file_record, temp_file_path, producer)
    # Close the producer
    producer.close()
    exit(0)
