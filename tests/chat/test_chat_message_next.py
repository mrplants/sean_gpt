######################
# /chat/message/next #
######################
# GET (protected, verified)
#   Get the next message in a chat. Chat UUID in header.
#
# This is implemented via SSE.  The client makes a POST request to push a new
# message to the chat.  The server begins streaming the AI response back to the
# client.  If the client makes another POST request, the server terminates the
# first SSE stream and then creates a new SSE stream for the new POST request.
#
# Importantly, the /chat/message/next endopint does not interact with the
# database.  It is simply a way to exchange messages with the assistant.  The
# database is updated when the client makes a POST request to /chat/message.

from sean_gpt.util.describe import describe

from ..user.fixtures import *
from ..util import *
from .util import *

@describe(
""" Tests that a basic, uninterrupted message exchange can occur.

- Create a chat.
- Create a message in the chat.
- Receive the entire response without interruption (it is a stream).
- Verify that both the message and the response can be retrieved.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
    mock_response_generator (Mock):  A mock AI generator.
""")
def test_create_message(verified_new_user, client, mock_response_generator):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Create a message.  The response will be streamed via SSE.
    request_kwargs = {
        "headers": {"Authorization": "Bearer " + verified_new_user["access_token"],
                    "X-Chat-ID": chat["id"]
                    },
        "json": {"content": "Hello, world! This is my first message in a chat."}
    }
    assistant_response = ''.join(stream_response("post","/chat/message",request_kwargs,client))
    # The assistant response is just the string content, without the ID of the message.
    # Verify that the message can be retrieved
    messages_response = client.get("/chat/message/next",
                          headers={
                              "Authorization": "Bearer " + verified_new_user["access_token"],
                              "X-Chat-ID": chat["id"]
                              })
    assert messages_response.status_code == 200
    assert messages_response.json()[0]["content"] == "Hello, world! This is my first message in a chat."
    assert messages_response.json()[1]["content"] == assistant_response