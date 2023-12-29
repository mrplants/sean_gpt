#################
# /chat/message #
#################
# POST (protected, verified)
#   Create a new message in a chat. Chat UUID in header.
# GET (protected, verified)
#   Get a paged list of chats. Filters in query string. Chat UUID in header.

from sean_gpt.util.describe import describe

from ..user.fixtures import *
from ..util import *
from .util import *

@describe(
""" Tests that a user can create a user-message in a chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_message_user(verified_new_user, client):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Create a message (no role defaults to user)
    response = client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my first message in a chat."})
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "id": "...",
    #     "content": "Hello, world! This is my first message in a chat.",
    #     "role": "user",
    #     "chat_id": "..."
    # }
    assert response.status_code == 201, f"Status should be 201, not {response.status_code}. Response: {response.text}"
    assert type(response.json()["id"]) == str
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "user"
    assert response.json()["chat_id"] == chat["id"]
    del response
    # Also test for explicitly stating "user"
    response = client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my first message in a chat.", "role":"user"})
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "id": "...",
    #     "content": "Hello, world! This is my first message in a chat.",
    #     "role": "user",
    #     "chat_id": "..."
    # }
    assert response.status_code == 201, f"Status should be 201, not {response.status_code}. Response: {response.text}"
    assert type(response.json()["id"]) == str
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "user"
    assert response.json()["chat_id"] == chat["id"]

@describe(
""" Tests that a user can create an assistant-message in a chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_message_assistant(verified_new_user, client):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Create a message (no role defaults to user)
    response = client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my first message in a chat.",
                                 "role": "assistant"})
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "id": "...",
    #     "content": "Hello, world! This is my first message in a chat.",
    #     "role": "assistant",
    #     "chat_id": "..."
    # }
    assert response.status_code == 201, f"Status should be 201, not {response.status_code}. Response: {response.text}"
    assert type(response.json()["id"]) == str
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "assistant"
    assert response.json()["chat_id"] == chat["id"]

@describe(
""" Tests that a user canonly create messages with roles "user" or "assistant".

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_message_invalid_role(verified_new_user, client):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Create a message (no role defaults to user)
    response = client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my first message in a chat.",
                                 "role": "invalid"})
    # The response should be:
    # HTTP/1.1 422 Unprocessable Entity
    assert response.status_code == 422, f"Status should be 422, not {response.status_code}. Response: {response.text}"
