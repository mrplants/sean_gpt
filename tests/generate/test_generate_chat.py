""" Tests for the /generate/chat endpoint. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
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

from unittest.mock import patch, Mock
import threading as th

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from sean_gpt.util.describe import describe
from ..util.chat import async_create_mock_streaming_openai_api
from ..util.check_routes import check_authorized_route

@describe(
""" Test GET endpoint for chat token generation.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_generate_chat_token_get(client: TestClient, verified_new_user: dict):
    # Create a chat generation token
    token_response = client.get(
        "/generate/chat/token",
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
def test_generate_chat(client: TestClient, verified_new_user: dict):
    # Create a chat generation token
    token = client.get(
        "/generate/chat/token",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"}).json()['token']

    # Create a variable to catch the response from the websocket.
    websocket_generated_response = ''
    expected_response = "Sample OpenAI response"
    # First, patch the OpenAI API to return a mock response.
    with patch('openai.resources.chat.AsyncCompletions.create',
               new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = (
            async_create_mock_streaming_openai_api(expected_response, delay=0.001)
        )
        # Put in a try block to catch any disconnect exceptions
        try:
            with client.websocket_connect(
                f"/generate/chat/ws?token={token}") as websocket:
                # The first messagein the exchange is the prior: a list of messages.
                websocket.send_json({
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
                })
                # The response is streamed back in chunks.
                # The server will disconnect when it is finished streaming.
                # Create a timer that will raise an exception if the server takes too long.
                def timeout_assertion():
                    websocket.close()
                    assert False, "The server took too long to respond."
                timer = th.Timer(10, timeout_assertion)
                timer.start()
                while True:
                    response = websocket.receive_text()
                    websocket_generated_response += response
                # All subsequent messages are the response.
        except WebSocketDisconnect:
            timer.cancel()

    # Check that the response is what we expect.
    assert websocket_generated_response == expected_response, (
        f"Expected response: {expected_response}. Received response: {websocket_generated_response}"
    )

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, client):
    check_authorized_route("GET",
                           "/generate/chat/token",
                           authorized_user=verified_new_user, client=client)
