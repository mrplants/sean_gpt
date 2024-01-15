""" Database utilities for the Sean GPT API. """
from typing import Annotated, Any

from sqlmodel import create_engine, SQLModel, Session, select
from fastapi import Depends
import aioredis

from ..config import settings
from .auth import get_password_hash
from .describe import describe

# Import all the models, so that they're registered with sqlmodel
from ..model.authenticated_user import AuthenticatedUser
from ..model.message import Message # pylint: disable=unused-import
from ..model.chat import Chat
from ..model.ai import AI
from ..model.verification_token import VerificationToken # pylint: disable=unused-import

# Module-level variable to store the database engine instance
_DB_ENGINE = None

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
        database_url = f"{settings.database_dialect}{settings.database_driver}://{settings.api_db_user}:{settings.api_db_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}" # pylint: disable=line-too-long
        _DB_ENGINE = create_engine(database_url, echo=settings.debug)
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
