""" Gets the messages for the specified chat. """
from fastapi import APIRouter, Header, HTTPException, status
from sqlmodel import select

from ....util.describe import describe
from ....util.database import SessionDep
from ....model.chat import Chat
from ....model.message import MessageRead
from ....util.user import AuthenticatedUserDep

router = APIRouter(prefix="/message")

@describe(
""" Gets the number of messages in the specified chat.

Note that the user can only get messages from chats that they own.

Args:
    x_chat_id (str): The chat id.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.

Returns:
    dict: The number of messages in the chat.
""")
@router.get("/len", status_code=status.HTTP_200_OK)
def get_message_len(*, # pylint: disable=missing-function-docstring
    x_chat_id: str = Header(),
    session: SessionDep,
    current_user: AuthenticatedUserDep
) -> dict:
    chat = session.exec(select(Chat).where(Chat.id == x_chat_id)).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    if not chat.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    return {'len':len(chat.messages)}

@describe(
""" Gets the messages for the specified chat.

Note that the user can only get messages from chats that they own. Query
can optionally include chat_index to identify a specific message.  Otherwise,
the first (oldest) message is returned.  This is chat_index=0.

If the chat_index is out of bounds or negative, raise a 404 error.

Args:
    x_chat_id (str): The chat id.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.
    chat_index (int): The chat index.

Returns:
    MessageRead: The message.
""")
@router.get("", status_code=status.HTTP_200_OK)
def get_message(*, # pylint: disable=missing-function-docstring
    x_chat_id: str = Header(),
    session: SessionDep,
    current_user: AuthenticatedUserDep,
    chat_index: int = 0
) -> MessageRead:
    chat = session.exec(select(Chat).where(Chat.id == x_chat_id)).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    if not chat.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    # Check for out of bounds.
    # If the chat_index is negative, raise an error.
    if chat_index < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Chat index must be positive.")
    # If the chat_index is beyond the end of the list, raise an error.
    if chat_index >= len(chat.messages):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    return chat.messages[chat_index]
