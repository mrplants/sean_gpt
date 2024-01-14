""" Test utilities related to Twilio.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

from contextlib import contextmanager

import httpx

from sean_gpt.util.describe import describe

@describe(
""" Test utility to retrieve the contents of the most recent SMS.
""")
def get_latest_sms(host: str) -> str:
    """ Retrieve the the most recent created SMS.

    Returns:
        The contents of the most recent SMS.
    """
    # Get the most recent SMS
    return httpx.get(
        f"{host}/mock/twilio/sms",
    ).json()

@describe(
""" Patch the Twilio validator.

Previously, this was done like:
# with patch('twilio.request_validator.RequestValidator.validate',
#         return_value=valid):

Args:
    valid (bool): Whether the validator should validate the request.
""")
@contextmanager
def patch_twilio_validator(host: str, valid: bool) -> None:
    prev_valid = httpx.get(f"{host}/mock/twilio/validator").json()["valid"]
    httpx.post(f"{host}/mock/twilio/validator", json={"valid": valid})
    yield
    httpx.post(f"{host}/mock/twilio/validator", json={"valid": prev_valid})

@describe(
""" Test utility to patch the OpenAI async completions API.

Args:
    openai_response (str): The simulated OpenAI response.
    delay (int, optional): The delay between each response from the OpenAI API. Defaults to 0.001.
""")
@contextmanager
def patch_openai_async_completions(host:str, openai_response: str, delay: int = 0.1):
    prev_response = httpx.get(f"{host}/mock/openai/async_completions").json()
    httpx.post(f"{host}/mock/openai/async_completions", json={
        "response":openai_response,
        "delay": delay
    })
    yield lambda: httpx.get(f"{host}/mock/openai/async_completions/call_args").json()
    httpx.post(f"{host}/mock/openai/async_completions", json=prev_response)
