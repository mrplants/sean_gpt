""" Database utilities for the Sean GPT API. """
from typing import Annotated, Any

from sqlmodel import create_engine, Session, select
from fastapi import Depends
import aioredis
from pymilvus import Collection, connections, DataType, FieldSchema, CollectionSchema, utility

from ..config import settings
from .auth import get_password_hash
from .describe import describe

# Import all the models, so that they're registered with sqlmodel
from ..model.authenticated_user import AuthenticatedUser
from ..model.message import Message
from ..model.verification_token import VerificationToken
from ..model.file import File, ShareSet, FileShareSetLink
from ..model.chat import Chat
from ..model.ai import AI

# Module-level variable to store the database engine instance
_DATABASE_URL = f"{settings.database_dialect}{settings.database_driver}://{settings.api_db_user}:{settings.api_db_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}" # pylint: disable=line-too-long
_DB_ENGINE = None

def create_milvus_collection_if_necessary():
    """Create the Milvus collection if it does not already exist."""

    # Connect to the Milvus server
    connections.connect(host=settings.milvus_host, port=settings.milvus_port)

    # Check if the collection already exists
    if settings.milvus_collection_name in utility.list_collections():
        print(f"Collection '{settings.milvus_collection_name}' already exists.")
        return

    # Define the fields
    chunk_id = FieldSchema(name="chunk_id", dtype=DataType.INT64, is_primary=True, auto_id=True)
    file_id = FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=36)  # For UUIDs
    chunk_location = FieldSchema(name="chunk_location", dtype=DataType.INT64)
    chunk_embedding = FieldSchema(name="chunk_embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)  # Default dimensionality
    chunk_txt = FieldSchema(name="chunk_txt", dtype=DataType.VARCHAR, max_length=1024)

    # Define the schema
    schema = CollectionSchema(fields=[chunk_id, file_id, chunk_location, chunk_embedding, chunk_txt], description="Chunk collection schema")

    # Create the collection
    milvus_collection = Collection(name=settings.milvus_collection_name, schema=schema)

    # Create the collection index
    index_param = {
        "metric_type": "L2",
        "index_type": "FLAT",
    }
    milvus_collection.create_index(field_name="chunk_embedding", index_params=index_param)

@describe(
""" Resets the database connection. """)
def reset_db_connection(): # pylint: disable=missing-function-docstring
    global _DB_ENGINE # pylint: disable=global-statement
    _DB_ENGINE = None

@describe(
""" Construct the database URL from the settings. """)
def get_db_engine(): # pylint: disable=missing-function-docstring
    global _DB_ENGINE # pylint: disable=global-statement
    if _DB_ENGINE is None:
        # dialect+driver://username:password@host:port/database
        _DB_ENGINE = create_engine(_DATABASE_URL, echo=settings.debug)
    return _DB_ENGINE

@describe(
""" Fill the database with the initial data. """)
def create_admin_if_necessary(): # pylint: disable=missing-function-docstring
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        # Create the admin user
        admin_user = AuthenticatedUser(
            phone=settings.user_admin_phone,
            hashed_password=get_password_hash(settings.user_admin_password),
            referrer_user_id="root",
            is_phone_verified=True,
            opted_into_sms=True,
        )
        # Check if the admin user exists
        select_admin = select(AuthenticatedUser).where(
            AuthenticatedUser.phone == settings.user_admin_phone)
        existing_admin_user = session.exec(select_admin).first()
        if not existing_admin_user:
            # Create the admin's unique twilio chat
            # Since the database is being created, need to also create the default AI model
            ai = AI(name=settings.app_default_ai_model)
            session.add(ai)
            twilio_chat = Chat(user_id=admin_user.id, name="Phone Chat", assistant_id=ai.id)
            session.add(twilio_chat)
            admin_user.twilio_chat_id = twilio_chat.id
            # Add the admin user to the database
            session.add(admin_user)
            session.commit()

@describe(
""" FastAPI dependency to get a database session. """)
def get_session(): # pylint: disable=missing-function-docstring
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        yield session

@describe(
""" FastAPI dependency to get a redis connection. """)
def get_redis_connection(): # pylint: disable=missing-function-docstring
    return aioredis.from_url(f"redis://{settings.redis_host}")

RedisConnectionDep = Annotated[Any, Depends(get_redis_connection)]

SessionDep = Annotated[Session, Depends(get_session)]
