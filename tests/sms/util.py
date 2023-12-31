from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient

from sean_gpt.config import settings
from sean_gpt.util.describe import describe

from ..chat.util import async_create_mock_streaming_openai_api

@describe(
""" Sends a mock text message via a POST request to the "/twilio" endpoint.

This function also mocks the OpenAI API and Twilio's RequestValidator to simulate
the behavior of the endpoint in a test environment.

Args:
    client (TestClient): The test client used to send the request.
    body (str, optional): The body of the text message. Defaults to 'This is a test twilio message.'.
    from_number (str, optional): The number the message is sent from. Defaults to '+14017122661'.
    to_number (str, optional): The number the message is sent to. Defaults to the Twilio phone number from settings.
    openai_response (str, optional): The simulated openai response.
    valid (bool, optional): Whether the Twilio RequestValidator should validate the request. Defaults to True.

Returns:
    Response: The response from the "/twilio" endpoint.
""")
def send_text(
    client: TestClient,
    body:str = 'This is a test twilio message.',
    from_number:str = '+14017122661',
    to_number:str = settings.twilio_phone_number,
    openai_response:str = "This is the simulated OpenAI resopnse.",
    valid:bool = True,
    delay:int = 0.001,
    patch_openai_api:bool = True):
    if patch_openai_api:
        with patch('openai.resources.chat.AsyncCompletions.create', new_callable=Mock) as mock_openai_api:
            mock_openai_api.side_effect = async_create_mock_streaming_openai_api("assistant message response", delay=delay)
            with patch('twilio.request_validator.RequestValidator.validate',
                    return_value=valid):
                response = client.post(
                    "/twilio",
                    json={
                        "MessageSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                        "SmsSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                        "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                        "MessagingServiceSid": "MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                        "From": from_number,
                        "To": to_number,
                        "Body": body,
                        "NumMedia": "0"
                    }
                )
    else:
        with patch('twilio.request_validator.RequestValidator.validate',
                return_value=valid):
            response = client.post(
                "/twilio",
                json={
                    "MessageSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    "SmsSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    "MessagingServiceSid": "MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    "From": from_number,
                    "To": to_number,
                    "Body": body,
                    "NumMedia": "0"
                }
            )
    return response

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