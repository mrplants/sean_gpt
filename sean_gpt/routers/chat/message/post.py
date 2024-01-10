""" Contains the POST method for creating a new message in a chat. """
from fastapi import APIRouter, Header, HTTPException, status, Body
from sqlmodel import select

from ....util.describe import describe
from ....util.database import SessionDep
from ....model.chat import Chat
from ....model.message import Message, MessageCreate, MessageRead
from ....util.user import AuthenticatedUserDep

router = APIRouter(prefix="/message")

@describe(
""" Creates a new message in the specified chat.

Note that the user can only create messages in chats that they own.

Args:
    x_chat_id (str): The ID of the chat to create the message in (header).
    message (MessageCreate): The message to create.
    session (Session): The database session (dependency).
    current_user (AuthenticatedUser): The current user (dependency).
    
Returns:
    The created message.
""")
@router.post("", status_code=status.HTTP_201_CREATED)
def create_message(*, # pylint: disable=missing-function-docstring
    x_chat_id: str = Header(),
    message: MessageCreate = Body(),
    session: SessionDep,
    current_user: AuthenticatedUserDep
) -> MessageRead:
    chat = session.exec(select(Chat).where(Chat.id == x_chat_id)).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    if not chat.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    message = Message(**message.model_dump(),
                      chat_id=chat.id,
                      chat_index=len(chat.messages))
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
