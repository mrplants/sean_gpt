from typing import Annotated

from .config import settings
from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends

from .auth_util import get_password_hash

# Import all the models, so that they're registered with sqlmodel
from .model.authentication.user import AuthenticatedUser
from .model.chats.message import Message
from .model.chats.chat import Chat
from .model.ai import AI

# dialect+driver://username:password@host:port/database
database_url = f"{settings.api_db_dialect}{settings.api_db_driver}://{settings.api_db_user}:{settings.api_db_password}@{settings.api_db_host}:{settings.api_db_port}/{settings.api_db_name}"
db_engine = create_engine(database_url, echo=settings.debug)

def create_tables():
    """ Creates the tables in the database."""
    SQLModel.metadata.create_all(db_engine)
    admin_user = AuthenticatedUser(phone=settings.admin_phone,
                                   hashed_password=get_password_hash(settings.admin_password))
    with Session(db_engine) as session:
        session.add(admin_user)
        session.commit()

def get_session():
    with Session(db_engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]