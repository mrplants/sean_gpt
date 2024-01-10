""" SMS utilities. """

from typing import Annotated

from twilio.rest import Client
from fastapi import Depends

from ..config import settings

def get_twilio_client():
    """ Get the Twilio client. """
    if settings.debug:
        return Client(settings.twilio_test_sid, settings.twilio_test_auth_token)
    else:
        return Client(settings.twilio_sid, settings.twilio_auth_token)

TwilioClientDep = Annotated[Client, Depends(get_twilio_client)]
