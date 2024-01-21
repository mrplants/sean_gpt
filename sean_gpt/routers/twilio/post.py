""" Twilio webhook endpoint """
from fastapi import APIRouter
from openai import AsyncOpenAI

from ...ai import default_ai
from ...util.database import SessionDep, RedisConnectionDep
from ...util.describe import describe
from ...config import settings
from .util import (
    TwilioGetUserDep,
    TwilioMessageDep,
    check_for_unsupported_msg,
    check_user_sms,
    chat_response_session,
    create_and_save_twiml_response,
    is_twilio_redirect,
    save_user_twilio_message,
    get_messages_openai,
    check_for_interrupts,
    trim_twiml_segments,
    num_twiml_segments
)

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

router = APIRouter(
    prefix="/twilio"
)

@describe(
""" Receives Twilio webhooks

Args:

Returns:
    TwiML.  The TwiML response.
""")
@router.post("")
async def twilio_webhook( # pylint: disable=missing-function-docstring
    incoming_message: TwilioMessageDep,
    current_user: TwilioGetUserDep,
    session: SessionDep,
    redis_conn: RedisConnectionDep):
    # Check if the user is trying to send an unsupported message type (whatsapp, MMS, etc.)
    unsupported_response = check_for_unsupported_msg(incoming_message)
    if unsupported_response:
        return unsupported_response

    # Check if the user exists and is opted into messaging
    check_user_response = check_user_sms(current_user, incoming_message, session)
    if check_user_response:
        return check_user_response

    # - Start a chat response session in case we get interrupted
    async with chat_response_session(current_user.twilio_chat_id,
                                     redis_conn,
                                     session) as (chat_response_session_id, chat, interrupt_pubsub):
        # Check if this is a new user (twilio chat has no messages yet)
        if not chat.messages:
            return await create_and_save_twiml_response(chat,
                                                  incoming_message,
                                                  settings.app_welcome_message,
                                                  session,
                                                  redis_conn)

        # If this is a redirect, don't save the user's message
        if not await is_twilio_redirect(incoming_message, redis_conn):
            save_user_twilio_message(chat, incoming_message, session)

        # - Begin streaming a response from openAI
        messages_openai = get_messages_openai(chat.id, session)

        response_stream = await openai_client.chat.completions.create(
            model=default_ai().name,
            messages=messages_openai,
            stream=True,
        )

        # Create the partial_response
        partial_response = ""
        async for chunk in response_stream:
            # Check the interrupt channel for interrupts
            # This will raise an exception if it finds one
            await check_for_interrupts(interrupt_pubsub, chat_response_session_id)

            partial_response += chunk.choices[0].delta.content or ""
            # Check if the partial response is over the character limit
            if num_twiml_segments(partial_response) > 1:
                print(f'Partial response is over the character limit: {partial_response}')
                trimmed_response = trim_twiml_segments(partial_response)
                return await create_and_save_twiml_response(chat,
                                                      incoming_message,
                                                      trimmed_response,
                                                      session,
                                                      redis_conn,
                                                      requires_redirect=True)

            # Check if the partial response has a message break
            if "|" in partial_response:
                print(f'Partial response has a message break: {partial_response}')
                # Break at that message and stop streaming.  Return the message.
                partial_response = partial_response.split("|")[0]
                return await create_and_save_twiml_response(chat,
                                                      incoming_message,
                                                      partial_response,
                                                      session,
                                                      redis_conn,
                                                      requires_redirect=True)
        return await create_and_save_twiml_response(chat,
                                              incoming_message,
                                              partial_response,
                                              session,
                                              redis_conn)
