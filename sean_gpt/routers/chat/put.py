import uuid

from fastapi import APIRouter, status, HTTPException, Header
from sqlmodel import select
from pydantic import BaseModel

from ...util.describe import describe
from ..user.util import AuthenticatedUserDep
from ...util.database import SessionDep
from ...model.chat import Chat

router = APIRouter(prefix="/chat")

class ChatUpdate(BaseModel):
    name: None|str = None

@describe(
""" Updates a chat in the database.

Args:
    update_params (ChatUpdate): The chat to update.
    chat_id (UUID): The id of the chat to update. Stored in the header.
    current_user (AuthenticatedUserDep): The current user.
    session (SessionDep): The database session.
""")
@router.put("", status_code=status.HTTP_204_NO_CONTENT)
def update_chat(*, update_params: ChatUpdate, x_chat_id: str = Header(), current_user: AuthenticatedUserDep, session: SessionDep):
    try:
        uuid.UUID(x_chat_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    chat = session.exec(select(Chat).where(Chat.id == x_chat_id)).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if update_params.name:
        chat.name = update_params.name
    session.commit()
    session.refresh(chat)
