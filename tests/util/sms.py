""" Utility functions for testing the Twilio endpoint.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

import xml.etree.ElementTree as ET
import uuid

import httpx

from sean_gpt.config import settings
from sean_gpt.util.describe import describe

from .mock import patch_twilio_validator, patch_openai_async_completions

@describe(
""" Sends a mock text message via a POST request to the "/twilio" endpoint.

This function also mocks the OpenAI API and Twilio's RequestValidator to simulate
the behavior of the endpoint in a test environment.

Args:
    client (TestClient): The test client used to send the request.
    body (str, optional): The body of the text message. Defaults to 'This is a test twilio message.'
    from_number (str, optional): The number the message is sent from. Defaults to '+14017122661'.
    to_number (str, optional): The number the message is sent to. Defaults to the Twilio phone
        number from settings.
    openai_response (str, optional): The simulated openai response.
    valid (bool, optional): Whether the Twilio RequestValidator should validate the request.
        Defaults to True.
    delay (int, optional): The delay between each response from the OpenAI API. Defaults to 0.001.
    patch_openai_api (bool, optional): Whether the OpenAI API should be mocked. Defaults to True.
    num_media (int, optional): The number of media files attached to the message. Defaults to 0.
    message_sid (str, optional): The message identifier.  Defaults to None, which triggers a random
        message ID.

Returns:
    Response: The response from the "/twilio" endpoint.
""")
# pylint: disable=too-many-arguments
def send_text(
    host: str,
    body:str = 'This is a test twilio message.',
    from_number:str = '+14017122661',
    to_number:str = settings.app_phone_number,
    openai_response:str = "This is the simulated OpenAI resopnse.",
    valid:bool = True,
    delay:int = 0.001,
    patch_openai_api:bool = True,
    num_media:int = 0,
    message_sid:str = None):
    if message_sid is None:
        message_sid = 'SM' + str(uuid.uuid4()).replace('-', '').upper()
    message = {
        "MessageSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "SmsSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "MessagingServiceSid": "MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "From": from_number,
        "To": to_number,
        "Body": body,
        "NumMedia": str(num_media)
    }
    with patch_twilio_validator(host, valid):
        if patch_openai_api:
            with patch_openai_async_completions(host, openai_response, delay=delay) as retrieve_call_args:
                response = httpx.post(
                    f"{host}/twilio",
                    json=message
                )
        else:
            httpx.post(f"{host}/mock/twilio/validator", json={"valid": valid})
            response = httpx.post(
                f"{host}/twilio",
                json=message
            )
    return response
#pylint: enable=too-many-arguments

@describe(
""" Parses a twiml http response and returns the message body.

This assumes that the twiml response is valid and contains a single Message.

Args:
    twiml: The twiml http response.

Returns:
    str: The message body.
""")
def parse_twiml_msg(twiml: str):
    return ET.fromstring(twiml.content).find("Message").text
