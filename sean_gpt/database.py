from typing import Annotated, Any

from sqlmodel import create_engine, SQLModel, Session, select
from fastapi import Depends
import aioredis

from .config import settings
from .util.auth import get_password_hash
from .util.describe import describe

# Import all the models, so that they're registered with sqlmodel
from .model.authenticated_user import AuthenticatedUser
from .model.message import Message
from .model.chat import Chat
from .model.ai import AI
from .model.verification_token import VerificationToken

# Module-level variable to store the database engine instance
_db_engine = None

@describe(
""" Resets the database connection. """)
def reset_db_connection():
    global _db_engine
    _db_engine = None

@describe(
""" Construct the database URL from the settings. """)
def get_db_engine():
    global _db_engine
    if _db_engine is None:
        # dialect+driver://username:password@host:port/database
        database_url = f"{settings.database_dialect}{settings.database_driver}://{settings.api_db_user}:{settings.api_db_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
        _db_engine = create_engine(database_url, echo=settings.debug)
    return _db_engine

@describe(
""" Fill the database with the initial data. """)
def create_admin_if_necessary():
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        # Create the admin user
        admin_user = AuthenticatedUser(
            phone=settings.user_admin_phone,
            hashed_password=get_password_hash(settings.user_admin_password),
            referrer_user_id="root",
            is_phone_verified=True,
        )
        # Check if the admin user exists
        select_admin = select(AuthenticatedUser).where(AuthenticatedUser.phone == settings.user_admin_phone)
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

@describe(""" Create and initialize the tables in the database. """)
def create_tables_if_necessary():
    db_engine = get_db_engine()
    SQLModel.metadata.create_all(db_engine)
    create_admin_if_necessary()

@describe(
""" FastAPI dependency to get a database session. """)
def get_session():
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        yield session

@describe(
""" FastAPI dependency to get a redis connection. """)
def get_redis_connection():
    return aioredis.from_url(f"redis://{settings.redis_host}")

RedisConnectionDep = Annotated[Any, Depends(get_redis_connection)]

SessionDep = Annotated[Session, Depends(get_session)]