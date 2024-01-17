""" Twilio utility functions """
from typing import Annotated, Optional

from fastapi import Request, HTTPException, Depends
from twilio.request_validator import RequestValidator
from sqlmodel import select

from ...config import settings
from ...model.authenticated_user import AuthenticatedUser
from ...model.twilio_message import TwilioMessage
from ...model.chat import Chat
from ...util.database import SessionDep
from ...model.ai import AI
from ...ai import default_ai

async def validate_twilio(request: Request):
    """ Validates a Twilio request.
    
    Args:
        request (Request): The request object containing the data sent by Twilio.
        
    Raises:
        HTTPException: If the request is invalid.
    """
    validator = RequestValidator(settings.twilio_auth_token)

    # Get the full URL that Twilio requested
    url = str(request.url)

    # Get the POST parameters
    form = await request.form()
    parameters = dict(form)

    # Get the signature from the `X-Twilio-Signature` header
    signature = request.headers.get('X-Twilio-Signature', '')
    # This isn't validating, so print out the entire request:  Header, body
    print('Request headers:')
    print(request.headers)
    print('Request body:')
    print(await request.body())

    # Validate the request
    if not validator.validate(url, parameters, signature):
        raise HTTPException(status_code=400, detail="Invalid Twilio Signature")

def twilio_get_or_create_user(
        incoming_message: TwilioMessage,
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

TwilioGetUserDep = Annotated[Optional[AuthenticatedUser], Depends(twilio_get_or_create_user)]
