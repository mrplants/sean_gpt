""" Tests for the /generate/chat endpoint. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

##################
# /generate/chat #
##################
# GET/POST (protected, verified)
#   Generate a chat completion response.
#
# This is implemented via websockets.  The client creates a websocket request and sends the
# conversation in the first message.  The server streams back the response.
#
# Importantly, the /generate endpoint does not interact with the database.  It is simply a means to
# generate content.  The database is updated when the client makes a POST request to /chat/message
# or some other endpoint.

#TODO: test that a connection cannot be made without a token
#TODO: test that a completion token will timeout

import threading as th
import json

import httpx
from websockets.sync.client import connect as connect_ws
from websockets.exceptions import ConnectionClosed

from sean_gpt.util.describe import describe
from ..util.check_routes import check_authorized_route
from ..util.mock import patch_openai_async_completions

@describe(
""" Test GET endpoint for chat token generation.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_generate_chat_token_get(sean_gpt_host: str, verified_new_user: dict):
    # Create a chat generation token
    token_response = httpx.get(
        f"{sean_gpt_host}/generate/chat/token",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"})
    # The response should be:
    # HTTP/1.1 200 OK
    # {
    #     "token": "..."
    # }
    assert token_response.status_code == 200, (
        f"Expected status code 200. Received status code {token_response.status_code}"
    )
    assert 'token' in token_response.json(), (
        f"Expected response to contain 'token'. Received response {token_response.json()}"
    )

@describe(
""" Test chat generation via websocket.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_generate_chat(sean_gpt_host: str, verified_new_user: dict):
    # Create a chat generation token
    token = httpx.get(
        f"{sean_gpt_host}/generate/chat/token",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"}).json()['token']

    # Create a variable to catch the response from the websocket.
    websocket_generated_response = ''
    expected_response = "Sample OpenAI response"
    # First, patch the OpenAI API to return a mock response.
    with patch_openai_async_completions(sean_gpt_host, expected_response, 0.001):
        # Put in a try block to catch any disconnect exceptions
        try:
            with connect_ws(f"{sean_gpt_host}/generate/chat/ws?token={token}".replace('http',
                                                                                      'ws')) as ws:
                # The first messagein the exchange is the prior: a list of messages.
                ws.send(json.dumps({
                    'action': 'chat_completion',
                    'payload': {
                        'conversation': [
                            {
                                "role": "user",
                                "content": "Hello, how are you?"
                            },
                            {
                                "role": "assistant",
                                "content": "I'm doing well, how are you?"
                            },
                            {
                                "role": "user",
                                "content": "I'm doing well too."
                            }
                        ]
                    }
                }))
                # The response is streamed back in chunks.
                # The server will disconnect when it is finished streaming.
                # Create a timer that will raise an exception if the server takes too long.
                def timeout_assertion():
                    ws.close()
                    assert False, "The server took too long to respond."
                timer = th.Timer(10, timeout_assertion)
                timer.start()
                while True:
                    response = ws.recv()
                    websocket_generated_response += response
                # All subsequent messages are the response.
        except ConnectionClosed:
            timer.cancel()

    # Check that the response is what we expect.
    assert websocket_generated_response == expected_response, (
        f"Expected response: {expected_response}. Received response: {websocket_generated_response}"
    )

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user: dict, sean_gpt_host:str):
    check_authorized_route("GET",
                           sean_gpt_host,
                           "/generate/chat/token",
                           authorized_user=verified_new_user)
