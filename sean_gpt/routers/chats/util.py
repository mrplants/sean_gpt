from typing import List
from uuid import UUID

from fastapi import HTTPException, Depends
from sqlmodel import select

from ..users.util import AuthenticatedUserDep
from ...database import SessionDep
from ...ai import default_ai
from ...model.ai import AI
from ...model.chats.chat import Chat, ChatRead
from ...model.chats.message import Message, MessageRead

# Retrieve a chat record without messages
def get_chat(chat_id: UUID, current_user: AuthenticatedUserDep, session: SessionDep) -> ChatRead:
    """ Retrieves a specific chat from the database.

    Raises HTTPException(404) if the chat does not exist or the user does not have access to the chat.

    Args:
        chat_id (int): The id of the chat to get.
        current_user (AuthenticatedUserDep): The current user.
        session (SessionDep): The database session.

    Returns:
        The chat associated with this chat id and user.
    """
    chat = session.exec(select(Chat).where(Chat.id == chat_id,
                                            Chat.user_id == current_user.id)).first()
    if not chat:
        raise HTTPException(status_code=404)
    return chat

def create_chat(*, chat_name: str|None = None, ai:AI = Depends(default_ai), current_user: AuthenticatedUserDep, session: SessionDep) -> ChatRead:
    """ Creates a new chat in the database.

    Args:
        chat_name (str): The name of the chat to create.
        current_user (AuthenticatedUserDep): The current user.
        session (SessionDep): The database session.

    Returns:
        The created chat.
    """
    chat = Chat(user_id=current_user.id, name=chat_name, assistant_id=ai.id)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat
