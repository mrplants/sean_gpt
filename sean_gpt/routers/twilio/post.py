from fastapi import APIRouter, Depends

from ...database import SessionDep
from ...model.twilio_message import TwilioMessage
from ...util.describe import describe

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
async def twilio_webhook(incoming_message: TwilioMessage, session: SessionDep):
    # - Retrieve the user
    # TODO: User creation logic
    # TODO: User referral code logic
    # - Retrieve the user's twilio chat
    # - Save the incoming message to the database (commit and refresh)
    # - Begin streaming a response from openAI
    # - When the response breaks the character limit, create the AI message.
    # - Save the AI message to the database (commit and refresh)
    # - Send the response to Twilio, with a redirect if the stream was incomplete.
    # TODO: Think about how to identify a redirect, so a user's message is not repeated.
    pass
