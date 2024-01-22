""" Twilio utility functions """
from typing import Annotated, Optional
from contextlib import asynccontextmanager
import uuid
from uuid import UUID
import math

from fastapi import Request, HTTPException, Depends, Response
from twilio.request_validator import RequestValidator
from sqlmodel import select, Session
import twilio.twiml.messaging_response as twiml

from ...config import settings
from ...model.authenticated_user import AuthenticatedUser
from ...model.twilio_message import TwilioMessage
from ...model.chat import Chat
from ...util.database import SessionDep
from ...model.ai import AI
from ...ai import default_ai
from ...model.message import Message

async def validate_twilio(request: Request):
    """ Validates a Twilio request.
    
    Args:
        request (Request): The request object containing the data sent by Twilio.
        
    Raises:
        HTTPException: If the request is invalid.
    """
    validator = RequestValidator(settings.twilio_auth_token)

    # Get the full URL that Twilio requested
    # Replace "http" with "https" because Twilio only sends requests over HTTPS and this endpoint is
    # behind a reverse proxy for SSL/TLS termination
    url = str(request.url)
    url = url.replace("http://", "https://")

    # Get the POST parameters
    form = await request.form()
    parameters = dict(form)

    # Get the signature from the `X-Twilio-Signature` header
    signature = request.headers.get('X-Twilio-Signature', '')

    # Validate the request
    if not validator.validate(url, parameters, signature):
        raise HTTPException(status_code=400, detail="Invalid Twilio Signature")

async def twilio_get_or_create_user(
        request: Request,
        session: SessionDep,
        ai:AI = Depends(default_ai)) -> Optional[AuthenticatedUser]:
    """ Gets or creates a user from a Twilio message.
    
    Args:
        incoming_message (TwilioMessage): The incoming message.
        session (SessionDep): The database session.
        ai (AI): The AI to use for this chat.
        
    Returns:
        Optional[AuthenticatedUser]: The user.
    """
    # - Get the incoming message
    incoming_message = TwilioMessage(**dict(await request.form()))

    # - Retrieve the user's phone number
    user_phone = incoming_message.from_
    # - Check if the user exists
    user = session.exec(select(AuthenticatedUser)
                        .where(AuthenticatedUser.phone == user_phone)).first()
    # - If not, check if the message body is a referral code
    if not user:
        referring_user = (session
                          .exec(select(AuthenticatedUser)
                                .where(AuthenticatedUser.referral_code == incoming_message.body))
                                .first())
        # - If so, create the user with the referral code
        if referring_user:
            user = AuthenticatedUser(
                phone=user_phone,
                referrer_user_id=referring_user.id,
                hashed_password='',
                is_phone_verified=True,
            )
            # Create the user's unique Twilio-only chat (all users have one)
            twilio_chat = Chat(user_id=user.id, name="Phone Chat", assistant_id=ai.id)
            user.twilio_chat_id = twilio_chat.id
            # Add the user's unique Twilio-only chat to the database
            session.add(twilio_chat)
            session.add(user)
            session.commit()
            session.refresh(user)
            # Create a twilio chat for the user

    else:
        # Make sure the user is phone verified
        if not user.is_phone_verified:
            user.is_phone_verified = True
            session.add(user)
            session.commit()
            session.refresh(user)
    # - Return the user
    return user

async def create_twilio_msg(request: Request) -> TwilioMessage:
    """ FastAPI dependency for generating twilio message models from the inbound request.
    Args:
        request (Request): The request object containing the data sent by Twilio.
    """
    yield TwilioMessage(**dict(await request.form()))

TwilioGetUserDep = Annotated[Optional[AuthenticatedUser], Depends(twilio_get_or_create_user)]
TwilioMessageDep = Annotated[TwilioMessage, Depends(create_twilio_msg)]

def check_for_unsupported_msg(msg: TwilioMessage) -> Response|None:
    """ Verify that this is not a whatsapp message or MMS.
    
    Args:
        msg (TwilioMessage): The message to check.
    
    Returns:
        Response:  The required "unsupported" response or None if supported message.
    """
    # - Verify that this is not a whatsapp message
    if msg.from_.startswith('whatsapp:'): # pylint: disable=no-member
        twiml_response = twiml.MessagingResponse()
        twiml_response.message(settings.app_no_whatsapp_message)
        return Response(content=twiml_response.to_xml(),
                        media_type="application/xml")
    # - Verify that this is not a MMS
    if msg.num_media > 0:
        twiml_response = twiml.MessagingResponse()
        twiml_response.message(settings.app_no_mms_message)
        return Response(content=twiml_response.to_xml(),
                        media_type="application/xml")
    return None

def check_user_sms(user: AuthenticatedUser, msg: TwilioMessage, session: Session) -> Response|None:
    """ Verifies that the user exists and has opted into SMS.
    
    Args:
        user (AuthenticatedUser): The user to check.
        
    Returns:
        Response:  The required response or None if valid user.
    """
    # - If the current_user could not be found, return a static message requesting referral code
    if not user:
        twiml_response = twiml.MessagingResponse()
        twiml_response.message(settings.app_request_referral_message)
        return Response(content=twiml_response.to_xml(),
                        media_type="application/xml")

    # - Verify that the user is opted into messaging
    if not user.opted_into_sms:
        # Check if the user has sent "AGREE" to opt in
        if msg.body.lower() == "agree": # pylint: disable=no-member
            user.opted_into_sms = True
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            twiml_response = twiml.MessagingResponse()
            twiml_response.message(settings.app_sms_opt_in_message)
            return Response(content=twiml_response.to_xml(),
                            media_type="application/xml")
    return None

@asynccontextmanager
async def chat_response_session(chat_id: UUID, redis_conn, session: Session):
    """ Context manager for a chat response session.
    
    Args:
        chat_id (UUID): The chat ID.
        redis_conn: The redis connection.
        session (Session): The database session.
        
    Yields:
        Tuple[str, Chat, ai.Message]: The chat response session ID, chat, and interrupt pubsub."""
    # # Create a chat response session ID.  Used to identify the request in the redis interrupts.
    chat_response_session_id = str(uuid.uuid4())

    # - Retrieve the chat
    chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()

    # Subscribe to stream interrupt events
    interrupt_channel_name = f'interrupt channel for chat with ID: {chat.id}'
    interrupt_pubsub = redis_conn.pubsub()
    await interrupt_pubsub.subscribe(interrupt_channel_name)

    # Check if the assistant is already responding
    if (await redis_conn.pubsub_numsub(interrupt_channel_name))[0][1] > 1:
        # Interrupt the other stream
        await redis_conn.publish(interrupt_channel_name, chat_response_session_id)

    yield chat_response_session_id, chat, interrupt_pubsub

async def create_and_save_twiml_response(chat:Chat, # pylint: disable=too-many-arguments
                                         incoming_message,
                                         msg_body:str,
                                         session:Session,
                                         redis_conn,
                                         requires_redirect:bool = False) -> Response:
    """ Creates and saves a twiml response.

    Args:
        chat (Chat): The chat.
        incoming_message (TwilioMessage): The incoming message.
        msg_body (str): The message body.
        session (Session): The database session.
        redis_conn: The redis connection.
        requires_redirect (bool): Whether the response requires a redirect.

    Returns:
        Response: The twiml response.
    """
    twiml_response = twiml.MessagingResponse()
    twiml_response.message(msg_body)
    # - Save the message to the database (commit and refresh)
    ai_message = Message(
        chat_index=len(chat.messages),
        chat_id=chat.id,
        role='assistant',
        content=msg_body,
    )
    session.add(ai_message)
    session.commit()
    # - Send the response to Twilio, with a redirect if the stream was incomplete.
    if requires_redirect:
        # Save that this is a redirect
        await redis_conn.set(f'multi-part message with SID: {incoming_message.message_sid}', 'True')
        twiml_response.redirect('./twilio')
    return Response(content=twiml_response.to_xml(),
                    media_type="application/xml")

async def is_twilio_redirect(msg: TwilioMessage, redis_conn) -> bool:
    """ Checks if a twilio message is a redirect.

    Args:
        msg (TwilioMessage): The twilio message.
        redis_conn: The redis connection.

    Returns:
        bool: Whether the message is a redirect.
    """
    return (await redis_conn.get(f'multi-part message with SID: {msg.message_sid}')) is not None

def save_user_twilio_message(chat, msg, session):
    """ Saves a user's twilio message to the database.

    Args:
        chat (Chat): The chat.
        msg (TwilioMessage): The twilio message.
        session (Session): The database session.
    """
    # - Save the incoming message to the database (commit and refresh)
    user_message = Message(
        chat_index=len(chat.messages),
        chat_id=chat.id,
        role='user',
        content=msg.body,
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)

def get_messages_openai(chat_id, session):
    """ Gets the messages in a chat in the OpenAI format.

    Args:
        chat_id (UUID): The chat ID.
        session (Session): The database session.

    Returns:
        List[Dict[str, str]]: The messages in the OpenAI format.
    """
    # Create the system and user messages
    openai_system_message = {
        "role": "system",
        "content": settings.app_ai_system_message,
    }
    # Retrieve the last X messages from the chat, in ascending order of chat_index
    # X = settings.app_chat_history_length
    messages = (session
                .exec(select(Message)
                      .where(Message.chat_id == chat_id)
                      .order_by(Message.chat_index.desc()) # pylint: disable=no-member
                      .limit(settings.app_chat_history_length-1)).all())

    # Put them in openai format, prepend the system message
    openai_messages = ([openai_system_message] +
                       [{"role": msg.role.value, "content": msg.content} for msg in messages][::-1])
    return openai_messages

async def check_for_interrupts(interrupt_pubsub, chat_response_session_id):
    """ Checks for interrupts to the stream.

    Args:
        interrupt_pubsub: The interrupt pubsub.
        chat_response_session_id (str): The chat response session ID.

    Raises:
        HTTPException: If the response was interrupted.
    """
    # Stop the stream and return early
    # Raise an error indicating that the response was interrupted
    message = await interrupt_pubsub.get_message(ignore_subscribe_messages=True)
    if message and message['data'].decode('utf-8') != chat_response_session_id:
        raise HTTPException("Twilio response interrupted.")

def num_twiml_segments(msg_body:str):
    """ Gets the number of TwiML segments required to send a message.

    Args:
        msg_body (str): The message body.

    Returns:
        int: The number of TwiML segments required to send the message.
    """
    return math.ceil(len(msg_body) / settings.app_max_sms_characters)

def trim_twiml_segments(msg_body, suffix=""):
    """ Trims a message to the maximum TwiML segment length.

    Args:
        msg_body (str): The message body.
        suffix (str): The suffix to append to the message.

    Returns:
        str: The trimmed message.
    """
    return msg_body[:settings.app_max_sms_characters-len(suffix)] + suffix
