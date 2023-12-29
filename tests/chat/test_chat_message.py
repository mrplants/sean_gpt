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
    # Create a message
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
    #     "chat_id": "...",
    #     "created_at": ..., # UNIX timestamp
    #     "chat_index": 0
    # }
    assert response.status_code == 201, f"Status should be 201, not {response.status_code}. Response: {response.text}"
    assert type(response.json()["id"]) == str
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "user"
    assert response.json()["chat_id"] == chat["id"]
    assert type(response.json()["created_at"]) == int
    assert response.json()["chat_index"] == 0
    del response
    # Also test for index incrementation
    response = client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my second message in a chat.", "role":"user"})
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "id": "...",
    #     "content": "Hello, world! This is my first message in a chat.",
    #     "role": "user",
    #     "chat_id": "...",
    #     "created_at": ..., # UNIX timestamp
    #     "chat_index": 1
    # }
    assert response.status_code == 201, f"Status should be 201, not {response.status_code}. Response: {response.text}"
    assert type(response.json()["id"]) == str
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "user"
    assert response.json()["chat_id"] == chat["id"]
    assert type(response.json()["created_at"]) == int
    assert response.json()["chat_index"] == 1

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
    # Create a message
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
    #     "chat_id": "...",
    #     "created_at": ..., # UNIX timestamp
    #     "chat_index": 0
    # }
    assert response.status_code == 201, f"Status should be 201, not {response.status_code}. Response: {response.text}"
    assert type(response.json()["id"]) == str
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "assistant"
    assert response.json()["chat_id"] == chat["id"]
    assert type(response.json()["created_at"]) == int
    assert response.json()["chat_index"] == 0

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
    # Create a message
    response = client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my first message in a chat.",
                                 "role": "invalid"})
    # The response should be:
    # HTTP/1.1 422 Unprocessable Entity
    assert response.status_code == 422, f"Status should be 422, not {response.status_code}. Response: {response.text}"

@describe(
""" Tests that a user can retrieve a list of messages in a chat.

The message response should be paged using limit and offset parameters.  They
are required.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_get_messages(verified_new_user, client):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Create a message
    client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my first message in a chat.", "role":"user"})
    # Create another message from an assistant
    client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": "Hello, world! This is my second message in a chat.",
                                 "role": "assistant"})
    # Get the messages
    response = client.get("/chat/message",
                          headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                   "X-Chat-ID": chat["id"]},
                          params={"limit": 1, "offset": 0})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # [
    #     {
    #         "id": "...",
    #         "content": "Hello, world! This is my first message in a chat.",
    #         "role": "user",
    #         "chat_id": "...",
    #         "created_at": ..., # UNIX timestamp
    #         "chat_index": 0
    #     }
    # ]
    assert response.status_code == 200, f"Status should be 200, not {response.status_code}. Response: {response.text}"
    assert type(response.json()) == list
    assert len(response.json()) == 1
    # Now add a bunch of messages to the chat
    for i in range(10):
        client.post("/chat/message",
                           headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                    "X-Chat-ID": chat["id"]
                                    },
                           json={"content": f"Hello, world! This is my {i+3}th message in a chat.",
                                 "role": "user"})
    # Get the messages
    response = client.get("/chat/message",
                          headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                   "X-Chat-ID": chat["id"]},
                          params={"limit": 5, "offset": 5})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # [...]
    assert response.status_code == 200, f"Status should be 200, not {response.status_code}. Response: {response.text}"
    assert type(response.json()) == list
    assert len(response.json()) == 5
    # Now test running off the edge of the list
    response = client.get("/chat/message",
                          headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                   "X-Chat-ID": chat["id"]},
                          params={"limit": 15, "offset": 5})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # [...]
    assert response.status_code == 200, f"Status should be 200, not {response.status_code}. Response: {response.text}"
    assert type(response.json()) == list
    assert len(response.json()) == 5
    # Now test starting after the end of the list
    response = client.get("/chat/message",
                          headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                   "X-Chat-ID": chat["id"]},
                          params={"limit": 15, "offset": 15})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # []
    assert response.status_code == 200, f"Status should be 200, not {response.status_code}. Response: {response.text}"
    assert type(response.json()) == list
    assert len(response.json()) == 0
    # Now test negative for the limit
    response = client.get("/chat/message",
                          headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                   "X-Chat-ID": chat["id"]},
                          params={"limit": -1, "offset": 0})
    # The response should be:
    # HTTP/1.1 422 Unprocessable Entity
    assert response.status_code == 422, f"Status should be 422, not {response.status_code}. Response: {response.text}"
    # Now test negative for the offset
    response = client.get("/chat/message",
                          headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                   "X-Chat-ID": chat["id"]},
                          params={"limit": 1, "offset": -1})
    # The response should be:
    # HTTP/1.1 422 Unprocessable Entity