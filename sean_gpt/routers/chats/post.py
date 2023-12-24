from openai import OpenAI
client = OpenAI()

from fastapi import APIRouter, Depends
from sqlmodel import select

from ..auth.utils import AuthenticatedUserDep
from ...database import SessionDep
from ...model.chats.chat import ChatRead, Chat
from ...model.chats.message import MessageRead, Message, MessageCreate
from ...model.ai import AI
from ...ai import default_ai
from .util import get_chat

router = APIRouter()

@router.post("/")
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

@router.post("/{chat_id}/message")
def create_message(*, user_msg:MessageCreate, ai:AI = Depends(default_ai), chat: ChatRead = Depends(get_chat), session: SessionDep) -> MessageRead:
    """ Creates a new message pair (user/assistant) in the database.

    This endpoint is effectively a push/get endpoint.  It stores the new user chat
    and then generates a response from the AI.  That response is stored in the database
    and returned to the user.

    Args:
        user_msg (MessageCreate): The user message.
        chat (ChatRead): The chat to add the message to.
        session (SessionDep): The database session.

    Returns:
        The created message.
    """
    # Before creating a Message, we need to know the number of messages in the chat.
    # This requires retrieving from the database, not just the count but all the
    # messages because we need them later when querying the model
    messages = session.exec(select(Message).where(Message.chat_id == chat.id)).all()
    chat_index = len(messages)
    user_msg = Message(**user_msg.dict(), chat_id=chat.id, chat_index=chat_index)

    # Store the user message in the database.
    session.add(user_msg)
    messages.append(user_msg)

    # To prepare the messages for the openai endpoint, we need to order them by
    # chat index and then convert them to a list of dictionaries, with only the
    # 'role' and 'content' keys
    messages = sorted(messages, key=lambda m: m.chat_index)
    oai_messages = [{"role": m.role, "content": m.content} for m in messages]
    # Generate a response from the openai endpoint.  In this case, the model name
    # is the default_ai name.
    response = client.chat.completions.create(
        model=ai.name,
        messages=oai_messages,
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print(response)

    # Create the assistant message from the response and store it in the database.
    assistant_msg = Message(
        chat_id=chat.id,
        chat_index=chat_index + 1,
        role="assistant",
        content=response.choices[0].message.content
    )
    session.add(assistant_msg)
    session.commit()
    session.refresh(assistant_msg)
    return assistant_msg