from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import select

from ..auth.utils import AuthenticatedUserDep
from ...database import SessionDep
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