from fastapi import APIRouter, Header, HTTPException, status, Query
from sqlmodel import select

from ....util.describe import describe
from ....database import SessionDep
from ....model.chat import Chat
from ....model.message import MessageRead
from ...user.util import AuthenticatedUserDep

router = APIRouter(prefix="/message")

@describe(
""" Gets the messages for the specified chat.

Note that the user can only get messages from chats that they own.

Args:
    x_chat_id (str): The ID of the chat to get the messages from (header).
    session (Session): The database session (dependency).
    current_user (AuthenticatedUser): The current user (dependency).
    offset (int): The offset to start getting messages from.
    limit (int): The maximum number of messages to get.

Returns:
    The messages.
""")
@router.get("", status_code=status.HTTP_200_OK)
def get_messages(*,
    x_chat_id: str = Header(),
    session: SessionDep,
    current_user: AuthenticatedUserDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100)
) -> list[MessageRead]:
    chat = session.exec(select(Chat).where(Chat.id == x_chat_id)).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    if not chat.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    # Check for out of bounds.
    # If the offset or limit are negative, raise an error.
    if offset < 0 or limit < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Offset and limit must be positive.")
    # If the offset is beyond the end of the list, return an empty list.
    if offset >= len(chat.messages):
        return []
    # If the range starts within, but extends beyond the end of the list,
    # return the list up to the end.
    if offset >= 0 and offset < len(chat.messages) and offset + limit > len(chat.messages):
        limit = len(chat.messages) - offset
    return chat.messages[offset:offset+limit]