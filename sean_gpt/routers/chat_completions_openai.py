import requests
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from ..database import db_engine
from ..model.chats.chat import ChatMessage, ChatRequest, Chat, Message
from ..model.authentication.user import User
from ..model.ai_model import AI
from .auth import get_current_user
from ..config import settings

router = APIRouter(
    prefix="/chat/completions",
    tags=["Chat Completion"],
)

def openai_helper(request: ChatRequest):
    """ Sends the request to the OpenAI API.

    Args:
        request (ChatRequest): The request to send to the OpenAI API.

    Returns:
        Response from OpenAI API.
    """
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(settings.openai_api_url, json=request.dict(), headers=headers)
        response.raise_for_status()  # Will raise HTTPError for 4xx/5xx responses
        return response.json()
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=response.status_code, detail=str(err))

@router.get("/chats/{chat_id}/messages", response_model=list[ChatMessage])
def get_chats(chat_id: str, current_user: Annotated[User, Depends(get_current_user)]):
    """ Gets a list of chat messages associated with this chat_id from the database.

    If the chat does not exist or if the user does not have access to the chat, this will return a 404.

    Args:
        chat_id (str): The chat_id to retrieve messages for.
        current_user (User): The current user.
    
    Returns:
        A list of chat messages associated with this chat_id.
    """
    with Session(db_engine) as session:
        chat = session.exec(select(Chat).where(Chat.owner_id == current_user.id)).first()
        if chat is None:
            raise HTTPException(status_code=404)
        
        

# An endpoint for retrieving a list of chats from the database
@router.get("/chats", response_model=list[Chat])
def get_chat_messages(current_user: Annotated[User, Depends(get_current_user)]):
    pass

# An endpoint for creating a new chat in the database
@router.post("/chats", response_model=Chat)
def create_chat(current_user: Annotated[User, Depends(get_current_user)]):
    pass

@router.post("/chats/{chat_id}/next_message", response_model=Message)
def chat_next_message(chat_id: str, msg: Message, current_user: Annotated[User, Depends(get_current_user)]):
    """ Gets the next message in the chat.

    This involves several steps:
    1.  Retrieve the chat from the database.
    2.  Retrieve all messages from this chat from the database.
    2b. Store the user's message in the database (since we know the index of the next message)
    3.  Pass the messages to an AI endpoint for completion.
    4.  Store the AI's response in the database.
    5.  Return the AI's response.

    Args:
        msg (ChatMessage): The user's next message in the chat.
        current_user (User): The current user.

    Returns:
        The AI's response to the user's message.
    """
    with Session(db_engine) as session:
        # 1.  Store the user's message in the database
        # First, check that the chat exists and that the user has access to it
        chat = session.exec(select(Chat).where(Chat.owner_id == current_user.id, Chat.id == chat_id)).first()
        if chat is None:
            raise HTTPException(status_code=404)

        # 2.  Retrieve all messages from this chat from the database
        chat_messages = session.exec(select(ChatMessage).where(ChatMessage.chat_id == chat_id)).all()

        # 2b. Store the user's message in the database (since we know the index of the next message)
        human_msg = ChatMessage(**msg.dict(), chat_id=chat_id, chat_index=len(chat_messages))
        session.add(human_msg)
        chat_messages.append(human_msg)

        # 3.  Pass the messages to an AI endpoint for completion.
        # Create a ChatRequest from the messages, in order of chat_index
        chat_messages.sort(key=lambda x: x.chat_index)
        messages = [Message(role=msg.role, content=msg.content) for msg in chat_messages]
        chat_request = ChatRequest(messages=messages)
        chat_response = openai_helper(chat_request)

        # 4.  Store the AI's response in the database.
        # If the AI model doesn't exist in the database, create it
        ai = session.exec(select(AI).where(AI.name == chat_request.model)).first()

        if ai is None:
            ai = AI(name=chat_request.model)
            session.add(ai)
        # Store the AI's response in the database.
        # Need to convert from openAI's response format to our own
        ai_msg = ChatMessage(
            chat_id=chat.id,
            chat_index=len(messages),
            content=chat_response["choices"][0]["message"]["content"],
            role="assistant",
        )
        session.add(ai_msg)
        session.commit()
        session.refresh(ai_msg)

    # 5.  Return the AI's response.
    return ai_msg

@router.post("/openai", dependencies=[Depends(get_current_user)])
def openai_chat_completions(request: ChatRequest):
    """ Passes the request verbatim to the OpenAI API.

    Args:
        request (ChatRequest): The request to pass to the OpenAI API.

    Returns:
        Response from OpenAI API.
    """
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }

    return openai_helper(request)