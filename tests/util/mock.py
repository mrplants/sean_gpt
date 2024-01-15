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
    get_response = httpx.get(
        f"{host}/mock/twilio/sms",
    )
    if get_response.is_error:
        print('error retrieving latest sms')
        print(get_response)
        print(get_response.text)
    return get_response.json()

@describe(
""" Patch the Twilio validator.

Args:
    valid (bool): Whether the validator should validate the request.
""")
@contextmanager
def patch_twilio_validator(host: str, valid: bool) -> None:
    prev_valid = httpx.get(f"{host}/mock/twilio/validator")
    if prev_valid.is_error:
        print('error retrieving twilio validator patch')
        print(prev_valid)
        print(prev_valid.text)
    prev_valid = prev_valid.json()['valid']
    post_response = httpx.post(f"{host}/mock/twilio/validator", data=str(valid).lower())
    if post_response.is_error:
        print('error posting twilio validator patch')
        print(post_response)
        print(post_response.text)
    yield
    repost_response = httpx.post(f"{host}/mock/twilio/validator", data=str(prev_valid).lower())
    if repost_response.is_error:
        print('error reposting twilio validator patch')
        print(repost_response)
        print(repost_response.text)

@describe(
""" Test utility to patch the OpenAI async completions API.

Args:
    openai_response (str): The simulated OpenAI response.
    delay (int, optional): The delay between each response from the OpenAI API. Defaults to 0.001.
""")
@contextmanager
def patch_openai_async_completions(host:str, openai_response: str, delay: float = 0.1):
    prev_response = httpx.get(f"{host}/mock/openai/async_completions")
    if prev_response.is_error:
        print('error retrieving openai patch')
        print(prev_response)
        print(prev_response.text)
    prev_response = prev_response.json()
    post_response = httpx.post(f"{host}/mock/openai/async_completions", json={
        "response":openai_response,
        "delay": delay
    })
    if post_response.is_error:
        print('error posting openai patch')
        print(post_response)
        print(post_response.text)
    yield lambda: httpx.get(f"{host}/mock/openai/async_completions/call_args").json()
    repost_response = httpx.post(f"{host}/mock/openai/async_completions", json=prev_response)
    if repost_response.is_error:
        print('error reposting openai patch')
        print(repost_response)
        print(repost_response.text)
