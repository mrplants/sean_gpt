from fastapi import APIRouter, Depends
from sqlmodel import select

from ..auth.utils import AuthenticatedUserDep
from ...database import SessionDep
from ...model.chats.chat import ChatRead, Chat
from ...model.chats.message import MessageRead, Message
from ...ai import default_ai
from .util import get_chat

router = APIRouter()

@router.post("/")
def create_chat(*, chat_name: str|None = None, current_user: AuthenticatedUserDep, session: SessionDep) -> ChatRead:
    """ Creates a new chat in the database.

    Args:
        chat_name (str): The name of the chat to create.
        current_user (AuthenticatedUserDep): The current user.
        session (SessionDep): The database session.

    Returns:
        The created chat.
    """
    chat = Chat(user_id=current_user.id, name=chat_name, assistant_id=default_ai.id)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat