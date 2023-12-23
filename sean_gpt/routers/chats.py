from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select

from .auth import AuthenticatedUserDep
from ..database import db_engine
from ..model.chats.chat import Chat, ChatRead
from ..model.chats.message import Message, MessageRead

router = APIRouter(
    prefix="/chats",
    tags=["Chat Completion"],
)

@router.get("/", response_model=List[ChatRead])
def get_chats(current_user: AuthenticatedUserDep):
    """ Gets a list of user's chat ids from the database.
    
    Args:
        current_user (AuthenticatedUserDep): The current user.
    
    Returns:
        A list of chat ids associated with this user.
    """
    with Session(db_engine) as session:
        chats = session.exec(select(Chat).where(Chat.user_id == current_user.id)).all()
        return chats

@router.get("/{chat_id}", response_model=List[MessageRead])
def get_chat(chat_id: UUID, current_user: AuthenticatedUserDep):
    """ Gets the chat messages with the specified chat id from the database.

    Raises HTTPException(404) if the chat does not exist or the user does not have access to the chat.
    
    Args:
        chat_id (int): The id of the chat to get messages from.
        current_user (AuthenticatedUserDep): The current user.
    
    Returns:
        A list of messages associated with this chat and user.
    """
    with Session(db_engine) as session:
        chat = session.exec(select(Chat).where(Chat.id == chat_id,
                                               Chat.user_id == current_user.id)).first()
        if not chat:
            raise HTTPException(status_code=404)
        messages = session.exec(select(Message).where(Message.chat_id == chat_id)).all()
        return messages
