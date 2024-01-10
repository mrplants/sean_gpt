from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter
from sqlmodel import select

from ...util.database import SessionDep
from ...model.chat import Chat, ChatRead
from ..user.util import AuthenticatedUserDep
from ...util.describe import describe

router = APIRouter(prefix="/chat")

@describe(
""" Gets a filtered list of chats for the current user.

Args:
    name (str): The name of the chat to filter by.
    id (UUID): The id of the chat to filter by.
    current_user (AuthenticatedUserDep): The current user.
    session (SessionDep): The database session.

Returns:
    A list of chats.
""")
@router.get("")
def get_chats(*, name: None|str = None, id: None|UUID = None, current_user: AuthenticatedUserDep, session: SessionDep) -> List[ChatRead]:
    query = select(Chat).where(Chat.user_id == current_user.id)
    if name:
        query = query.where(Chat.name == name)
    if id:
        query = query.where(Chat.id == id)
    return session.exec(query).all()