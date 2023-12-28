from uuid import UUID
from typing import List, Annotated

from fastapi import Depends, APIRouter
from sqlmodel import select

from ...database import SessionDep
from ...model.chat import Chat, ChatRead
from ...model.message import Message, MessageRead
from ..users.util import AuthenticatedUserDep
from .util import get_chat

router = APIRouter()

@router.get("/")
def get_chats(current_user: AuthenticatedUserDep, session: SessionDep) -> List[ChatRead]:
    """ Gets a list of user's chat ids from the database.
    
    Args:
        current_user (AuthenticatedUserDep): The current user.
    
    Returns:
        A list of chat ids associated with this user.
    """
    chats = session.exec(select(Chat).where(Chat.user_id == current_user.id)).all()
    return chats

# Retrieve a single chat recrod without messages
@router.get("/{chat_id}")
def get_chat(chat: ChatRead = Depends(get_chat)) -> ChatRead:
    """ Gets a chat with the specified chat id from the database.
    
    Args:
        chat (ChatRead): The chat to get.
    
    Returns:
        A chat associated with this chat id and user.
    """
    return chat

@router.get("/{chat_id}/messages")
def get_chat_messages(*, chat: ChatRead = Depends(get_chat), session: SessionDep) -> List[MessageRead]:
    """ Gets the chat messages with the specified chat id from the database.

    Raises HTTPException(404) if the chat does not exist or the user does not have access to the chat.
    
    Args:
        chat (ChatRead): The chat to get messages from.
        session (SessionDep): The database session.
    
    Returns:
        A list of messages associated with this chat and user.
    """
    messages = session.exec(select(Message).where(Message.chat_id == chat.id)).all()
    return messages
