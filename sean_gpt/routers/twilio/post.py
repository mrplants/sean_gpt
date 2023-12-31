from fastapi import APIRouter
from fastapi.responses import Response
from sqlmodel import select
from openai import AsyncOpenAI
import twilio.twiml.messaging_response as twiml

from ...database import SessionDep
from ...model.twilio_message import TwilioMessage
from ...model.chat import Chat
from ...model.message import Message
from ...util.describe import describe
from ...config import settings
from .util import TwilioGetUserDep

openai_client = AsyncOpenAI()

router = APIRouter(
    prefix="/twilio"
)

@describe(
""" Receives Twilio webhooks

Args:
    request (Request): The request object containing the data sent by Twilio.

Returns:
    TwiML.  The TwiML response.
""")
@router.post("")
async def twilio_webhook(incoming_message: TwilioMessage, current_user: TwilioGetUserDep, session: SessionDep):
    # - If the current_user could not be found, return a static message requesting referral code
    if not current_user:
        twiml_response = twiml.MessagingResponse()
        twiml_response.message(settings.twilio_request_referral_message)
        return Response(content=twiml_response.to_xml(),
                        media_type="application/xml")
    # - Retrieve the user's twilio chat
    twilio_chat = session.exec(select(Chat).where(Chat.id == current_user.twilio_chat_id)).first()
    session.add(twilio_chat)
    twilio_chat.is_assistant_responding = True
    session.commit()
    session.refresh(twilio_chat)
    # Check if this is a new user (twilio chat has no messages yet)
    # If so, send the static welcome message.
    if not twilio_chat.messages:
        twiml_response = twiml.MessagingResponse()
        twiml_response.message(settings.twilio_welcome_message)
        return Response(content=twiml_response.to_xml(),
                        media_type="application/xml")
    # - Save the incoming message to the database (commit and refresh)
    user_message = Message(
        chat_index=len(twilio_chat.messages),
        chat_id=twilio_chat.id,
        role='user',
        content=incoming_message.body,
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)
    # - Begin streaming a response from openAI
    # Create the system and user messages
    openai_system_message = {
        "role": "system",
        "content": settings.twilio_ai_system_message,
    }
    # Retrieve the last X messages from the chat, in ascending order of chat_index
    # X = settings.chat_history_length
    messages = session.exec(select(Message).where(Message.chat_id == twilio_chat.id).order_by(Message.chat_index.desc()).limit(settings.chat_history_length-1)).all()
    # Put them in openai format, prepend the system message
    openai_messages = [openai_system_message] + [{"role": msg.role.value, "content": msg.content} for msg in messages][::-1]
    # TODO: Incorporate different AI agents
    response_stream = await openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=openai_messages,
        stream=True,
    )
    # Create the partial_response
    partial_response = ""
    requires_redirect = False
    async for chunk in response_stream:
        partial_response += chunk.choices[0].delta.content or ""
        # Check if the partial response is over the character limit
        if len(partial_response) > settings.twilio_max_message_characters:
            # Break at the character limit, add an ellipsis emoji, and stop streaming.  Return the message.
            partial_response = partial_response[:settings.twilio_max_message_characters] + "…"
            requires_redirect = True
            break
        # Check if the partial response has a message break
        if "|" in partial_response:
            # Break at that message and stop streaming.  Return the message.
            partial_response = partial_response.split("|")[0]
            requires_redirect = True
            break
    # - Save the AI message to the database (commit and refresh)
    ai_message = Message(
        chat_index=len(twilio_chat.messages),
        chat_id=twilio_chat.id,
        role='assistant',
        content=partial_response,
    )
    session.add(ai_message)
    session.commit()
    session.refresh(ai_message)
    # - Send the response to Twilio, with a redirect if the stream was incomplete.
    twiml_response = twiml.MessagingResponse()
    twiml_response.message(ai_message.content)
    if requires_redirect:
        twiml_response.redirect('./')
    return Response(content=twiml_response.to_xml(),
                    media_type="application/xml")
    # TODO: Think about how to identify a redirect, so a user's message is not repeated.