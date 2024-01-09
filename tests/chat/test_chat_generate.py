""" Tests for the /chat/generate endpoint. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

######################
# /chat/generate #
######################
# GET/POST (protected, verified)
#   Generate a chat completion response.
#
# This is implemented via SSE.
#
# The client initiates a stream request by sending a POST with a list of
# messages.  The server responds with a stream_token.
# The client then makes a GET request with the stream_token.  The server
# responds with a SSE stream.
#
# If the client makes another stream POST request, the server terminates the
# first SSE stream.
#
# Importantly, the /chat/message/next endopint does not interact with the
# database.  It is simply a way to exchange messages with the assistant.  The
# database is updated when the client makes a POST request to /chat/message.

from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe
from ..util.chat import async_create_mock_streaming_openai_api, stream_response
from ..util.check_routes import check_verified_route

@describe(
""" Tests that a stream session token is returned.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_get_stream_session_token(verified_new_user: dict, client: TestClient):
    token_response = client.post("/chat/generate",
                        headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                        json=[
                                {"role" : "user",
                                 "content": "Hello, world! This is my first message in a chat."},
                                {"role" : "assistant",
                                 "content": "Hello, world! This is my second message in a chat."}
                            ])

    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # {
    #     "stream_token": "..."
    # }
    assert token_response.status_code == 200, (
        f"Check that the response is 200 OK.  Response: {token_response.status_code}"
    )
    assert "stream_token" in token_response.json(), (
        "Check that the response contains a stream_token."
    )

@describe(
""" Tests that a basic stream can be created.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_stream(verified_new_user: dict, client: TestClient):
    # Create a stream token
    token_response = client.post("/chat/generate",
                        headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                        json=[
                                {"role" : "user",
                                 "content": "Hello, world! This is my first message in a chat."},
                                {"role" : "assistant",
                                 "content": "Hello, world! This is my second message in a chat."},
                                {"role" : "user",
                                 "content": "Hello, world! another user message."},
                            ])
    assert "stream_token" in token_response.json(), (
        "Check that the post response contains a stream_token."
    )
    # Create a stream
    with patch('openai.resources.chat.AsyncCompletions.create',
               new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = (
            async_create_mock_streaming_openai_api("Sample OpenAI response", delay=0.001)
        )
        response = ''.join(stream_response("/chat/generate", {
            "headers": {
                "Authorization": "Bearer " + verified_new_user["access_token"],
                "X-Chat-Stream-Token": token_response.json()["stream_token"]
            }
        },client))
    assert response == "Sample OpenAI response", "Check that the stream response is correct."

# # @describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, client):
    # First, create a stream token
    token = client.post("/chat/generate",
                        headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                        json=[]
                        ).json()['stream_token']
    # Check the routes
    check_verified_route("post", "/chat/generate", verified_new_user, client,
                         json=[])
    with patch('openai.resources.chat.AsyncCompletions.create',
               new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = (
            async_create_mock_streaming_openai_api("Sample OpenAI response", delay=0.001)
        )
        check_verified_route("get", "/chat/generate", verified_new_user, client,
                            headers={
                                "X-Chat-Stream-Token": token
                            })
