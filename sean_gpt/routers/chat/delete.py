""" Deletes a chat from the database. """

from fastapi import APIRouter, Header, HTTPException, status
from sqlmodel import select

from ...util.describe import describe
from ...util.database import SessionDep
from ...model.chat import Chat
from ..user.util import AuthenticatedUserDep

router = APIRouter(prefix="/chat")

@describe(
""" Deletes a chat from the database.

A user can only delete their own chats.

Args:
    chat_id (UUID): The id of the chat to delete. Stored in the header.
    current_user (AuthenticatedUserDep): The current user.
    session (SessionDep): The database session.
""")
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat( # pylint: disable=missing-function-docstring
    *,
    x_chat_id: str = Header(),
    current_user: AuthenticatedUserDep,
    session: SessionDep):
    chat = session.exec(select(Chat).where(Chat.id == x_chat_id)).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    session.delete(chat)
    session.commit()
    return chat
