""" Tests for the /chat/message endpoint.
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

#################
# /chat/message #
#################
# POST (protected, verified)
#   Create a new message in a chat. Chat UUID in header.
# GET (protected, verified)
#   Get a message from a chat. Filters in query string. Chat UUID in header.
#   If no filters are provided, will return first chat message.
#   Filters:
#     chat_index (int):  The index of the message in the chat. 0 is oldest.
# GET /len (protected, verified)
#   Get the number of messages in a chat. Chat UUID in header.

from sean_gpt.util.describe import describe

from ..util.check_routes import check_verified_route

@describe(
""" Tests that a user can retrieve the number of messages in a chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_get_messages_len(verified_new_user, client):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Create a message
    client.post(
        "/chat/message",
        headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                 "X-Chat-ID": chat["id"]
        },
        json={"content": "Hello, world! This is my first message in a chat.", "role":"user"})
    # Create another message from an assistant
    client.post(
        "/chat/message",
        headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                 "X-Chat-ID": chat["id"]
        },
        json={"content": "Hello, world! This is my second message in a chat.",
              "role": "assistant"})
    # Get the messages
    response = client.get(
        "/chat/message/len",
        headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                 "X-Chat-ID": chat["id"]})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # {
    #     "len": 2
    # }
    assert response.status_code == 200, (
        f"Status should be 200, not {response.status_code}. Response: {response.text}"
    )
    assert response.json()["len"] == 2

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
    response = client.post(
        "/chat/message",
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
    assert response.status_code == 201, (
        f"Status should be 201, not {response.status_code}. Response: {response.text}"
    )
    assert isinstance(response.json()["id"], str)
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "user"
    assert response.json()["chat_id"] == chat["id"]
    assert isinstance(response.json()["created_at"], int)
    assert response.json()["chat_index"] == 0
    del response
    # Also test for index incrementation
    response = client.post(
        "/chat/message",
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
    assert response.status_code == 201, (
        f"Status should be 201, not {response.status_code}. Response: {response.text}"
    )
    assert isinstance(response.json()["id"], str)
    assert response.json()["content"] == "Hello, world! This is my second message in a chat."
    assert response.json()["role"] == "user"
    assert response.json()["chat_id"] == chat["id"]
    assert isinstance(response.json()["created_at"], int)
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
    assert response.status_code == 201, (
        f"Status should be 201, not {response.status_code}. Response: {response.text}"
    )
    assert isinstance(response.json()["id"], str)
    assert response.json()["content"] == "Hello, world! This is my first message in a chat."
    assert response.json()["role"] == "assistant"
    assert response.json()["chat_id"] == chat["id"]
    assert isinstance(response.json()["created_at"], int)
    assert response.json()["chat_index"] == 0

@describe(
""" Tests that a user can only create messages with roles "user" or "assistant".

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
    assert response.status_code == 422, (
        f"Status should be 422, not {response.status_code}. Response: {response.text}"
    )

@describe(
""" Tests that a user can retrieve messages in a chat.

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
    client.post(
        "/chat/message",
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
    # Get a message from the chat
    # No queries should return the oldest message
    response = client.get("/chat/message",
                            headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                     "X-Chat-ID": chat["id"]})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # {
    #     "id": "...",
    #     "content": "Hello, world! This is my first message in a chat.",
    #     "role": "user",
    #     "chat_id": "...",
    #     "created_at": ..., # UNIX timestamp
    #     "chat_index": 0
    # }
    assert response.status_code == 200, (
        f"Status should be 200, not {response.status_code}. Response: {response.text}"
    )
    assert isinstance(response.json()["id"], str), (
        f"ID should be a string, not {type(response.json()['id'])}. Response: {response.text}"
    )
    assert response.json()["content"] == "Hello, world! This is my first message in a chat.", (
        "Content should be 'Hello, world! This is my first message in a chat.', "
        f"not {response.json()['content']}. Response: {response.text}"
    )
    assert response.json()["role"] == "user",(
        f"Role should be 'user', not {response.json()['role']}. Response: {response.text}"
    )
    assert response.json()["chat_id"] == chat["id"], (
        f"Chat ID should be {chat['id']}, not {response.json()['chat_id']}. "
        "Response: {response.text}"
    )
    assert isinstance(response.json()["created_at"], int), (
        f"Created at should be an int, not {type(response.json()['created_at'])}. "
        "Response: {response.text}")
    assert response.json()["chat_index"] == 0, (
        f"Chat index should be 0, not {response.json()['chat_index']}. Response: {response.text}")

    # Get a message from the chat
    # Querying for chat_index=1 should return the second message
    response = client.get("/chat/message",
                            headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                     "X-Chat-ID": chat["id"]},
                            params={"chat_index": 1})
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # {
    #     "id": "...",
    #     "content": "Hello, world! This is my second message in a chat.",
    #     "role": "assistant",
    #     "chat_id": "...",
    #     "created_at": ..., # UNIX timestamp
    #     "chat_index": 1
    # }
    assert response.status_code == 200, (
        f"Status should be 200, not {response.status_code}. Response: {response.text}")
    assert isinstance(response.json()["id"], str), (
        f"ID should be a string, not {type(response.json()['id'])}. Response: {response.text}")
    assert response.json()["content"] == "Hello, world! This is my second message in a chat.", (
        "Content should be 'Hello, world! This is my second message in a chat.', "
        f"not {response.json()['content']}. Response: {response.text}")
    assert response.json()["role"] == "assistant", (
        f"Role should be 'assistant', not {response.json()['role']}. Response: {response.text}")
    assert response.json()["chat_id"] == chat["id"], (
        f"Chat ID should be {chat['id']}, not {response.json()['chat_id']}. "
        f"Response: {response.text}")
    assert isinstance(response.json()["created_at"], int), (
        f"Created at should be an int, not {type(response.json()['created_at'])}. "
        f"Response: {response.text}")
    assert response.json()["chat_index"] == 1, (
        f"Chat index should be 1, not {response.json()['chat_index']}. Response: {response.text}")

    # Make sure you that negative and out-of-bounds indices return 404
    response = client.get("/chat/message",
                            headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                     "X-Chat-ID": chat["id"]},
                            params={"chat_index": -1})
    # The response should be:
    # HTTP/1.1 404 Not Found
    assert response.status_code == 404, (
        f"Status should be 404, not {response.status_code}. Response: {response.text}")

    response = client.get("/chat/message",
                            headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                                     "X-Chat-ID": chat["id"]},
                            params={"chat_index": 2})
    # The response should be:
    # HTTP/1.1 404 Not Found
    assert response.status_code == 404, (
        f"Status should be 404, not {response.status_code}. Response: {response.text}")

@describe(
""" Tests that a user cannot create a message in a chat that they do not own.

Args:
    verified_new_user (dict):  A verified user.
    verified_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_message_unauthorized(verified_new_user, admin_user, client):
    # Create a chat
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + admin_user["access_token"],},
                       json={}).json()
    # Create a message
    response = client.post(
        "/chat/message",
        headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                 "X-Chat-ID": chat["id"]},
        json={"content": "Hello, world! This is my first message in a chat.", "role":"user"})
    # The response should be:
    # HTTP/1.1 404 Not Found
    assert response.status_code == 404, (
        f"Status should be 404, not {response.status_code}. Response: {response.text}")

@describe(
""" Tests that a user cannot create a message in a chat that does not exist.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_message_not_found(verified_new_user, client):
    # Create a message
    response = client.post(
        "/chat/message",
        headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                 "X-Chat-ID": "00000000-0000-0000-0000-000000000000"},
        json={"content": "Hello, world! This is my first message in a chat.", "role":"user"})
    # The response should be:
    # HTTP/1.1 404 Not Found
    assert response.status_code == 404, (
        f"Status should be 404, not {response.status_code}. Response: {response.text}")

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, client):
    # First, create a chat for messages
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Check the routes
    check_verified_route(
        "post",
        "/chat/message",
        verified_new_user,
        client,
        json={"content": "Hello, world! This is my first message in a chat.", "role":"user"},
        headers={"X-Chat-ID": chat["id"]})
    check_verified_route(
        "get",
        "/chat/message",
        verified_new_user,
        client,
        headers={"X-Chat-ID": chat["id"]})
