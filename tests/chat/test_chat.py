""" Tests for the /chat endpoint.
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

#########
# /chat #
#########
# POST (protected, verified):  Create a new chat
# PUT (protected, verified):  Update a chat, UUID in header.
# GET (protected, verified):  Get a list of chats, filters in query string.
# DELETE (protected, verified):  Delete a chat, UUID in header.
#
# A chat is between an assistant and a user.  When the user posts, the assistant
# responds.  The user can interrupt the AI.  Therefore, the server endpoint
# cannot be stateless.  It keeps track of the ongoing activity of an assistant
# responding to a user and interrupts that activity if another POST is made to
# the same chat.  The assistant is then responding to the chat activity,
# including the user's interruption.
#
# The states of a chat are:
# - is_assistant_responding = True
# - is_assistant_responding = False


# TODO: Make it so that backend does not allow deleting phone chat.

import random

import httpx

from sean_gpt.util.describe import describe

from ..util.check_routes import check_verified_route

@describe(
""" Test that a user can create a chat. 

The chat name is optional.  Test that it works with and without a name.  After
creating the chat, test that it appears in the list of chats for the user.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_chat(verified_new_user: dict, sean_gpt_host: str):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response_1 = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "name": "...",
    #     "id": "...",
    #     "user_id": "...",
    #     "assistant_id": "...",
    # }   "is_assistant_responding": false
    # }
    assert chat_response_1.status_code == 201, (
        f'incorrect status code: {chat_response_1.status_code}, response: {chat_response_1.json()}')
    assert chat_response_1.headers["content-type"] == "application/json"
    assert chat_response_1.json()["name"] == test_chat_name
    assert isinstance(chat_response_1.json()["id"], str)
    assert chat_response_1.json()["user_id"] == verified_new_user["id"]
    assert isinstance(chat_response_1.json()["assistant_id"], str)
    assert not chat_response_1.json()["is_assistant_responding"]

    # Create a chat without a name.
    chat_response_2 = httpx.post(f"{sean_gpt_host}/chat", json={}, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "name": "",
    #     "id": "...",
    #     "user_id": "...",
    #     "assistant_id": "...",
    #     "is_assistant_responding": false
    # }
    assert chat_response_2.status_code == 201, (
        f'incorrect status code: {chat_response_2.status_code}, response: {chat_response_2.json()}')
    assert chat_response_2.headers["content-type"] == "application/json"
    assert chat_response_2.json()["name"] == ""
    assert isinstance(chat_response_2.json()["id"], str)
    assert chat_response_2.json()["user_id"] == verified_new_user["id"]
    assert isinstance(chat_response_2.json()["assistant_id"], str)
    assert not chat_response_2.json()["is_assistant_responding"]

    # Check that both chats appears in the list of chats for the user.
    response_list = httpx.get(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # [
    #     {
    #         "name": "...",
    #         "id": "...",
    #         "user_id": "...",
    #         "assistant_id": "...",
    #         "is_assistant_responding": false
    #     },...
    # ]
    assert response_list.status_code == 200, (
        f'incorrect status code: {response_list.status_code}, response: {response_list.json()}')
    assert response_list.headers["content-type"] == "application/json"
    assert chat_response_1.json() in response_list.json()
    assert chat_response_2.json() in response_list.json()
    # clean up by deleting the chat 1
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response_1.json()["id"]
    })
    # clean up by deleting the chat 2
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response_2.json()["id"]
    })

@describe(
""" Test that a user can delete a chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_delete_chat(verified_new_user: dict, sean_gpt_host: str):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.status_code == 201, (
        f'incorrect status code: {chat_response.status_code}, response: {chat_response.json()}')

    # Delete the chat.
    delete_response = httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response.json()["id"]
    })
    # The response should be:
    # HTTP/1.1 204 No Content
    assert delete_response.status_code == 204, (
        f'incorrect status code: {delete_response.status_code}, response: {delete_response.json()}')

    # Check that the chat no longer appears in the list of chats for the user.
    response_list = httpx.get(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.json() not in response_list.json()

@describe(
""" Test that a user cannot delete a chat that does not belong to them.

Args:
    admin_user (dict):  An admin user.
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_delete_other_chat(admin_user: dict, verified_new_user: dict, sean_gpt_host: str):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.status_code == 201, (
        f'incorrect status code: {chat_response.status_code}, response: {chat_response.json()}')

    # Delete the chat as the admin user.
    delete_response = httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {admin_user['access_token']}",
        "X-Chat-ID": chat_response.json()["id"]
    })
    # The response should be:
    # HTTP/1.1 404 Not Found
    # Content-Type: application/json
    # {
    #     "detail": "Chat not found"
    # }
    assert delete_response.status_code == 404, (
        f'incorrect status code: {delete_response.status_code}, response: {delete_response.json()}')
    assert delete_response.headers["content-type"] == "application/json"
    assert delete_response.json()["detail"] == "Chat not found"

    # Check that the chat still appears in the list of chats for the user.
    response_list = httpx.get(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.json() in response_list.json()

    # clean up by deleting the chat
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response.json()["id"]
    })

@describe(
""" Test that a user can get a list of chats.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_get_chat_list(verified_new_user: dict, sean_gpt_host: str):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.status_code == 201, (
        f'incorrect status code: {chat_response.status_code}, response: {chat_response.json()}')

    # Check that the chat appears in the list of chats for the user.
    response_list = httpx.get(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # [
    #     {
    #         "name": "...",
    #         "id": "...",
    #         "user_id": "...",
    #         "assistant_id": "...",
    #         "is_assistant_responding": false
    #     },...
    # ]
    assert response_list.status_code == 200, (
        f'incorrect status code: {response_list.status_code}, response: {response_list.json()}')
    assert response_list.headers["content-type"] == "application/json"
    assert chat_response.json() in response_list.json()
    # clean up by deleting the chat
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response.json()["id"]
    })

@describe(
""" Test that a user can filter the list of chats.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_filter_chat_list(verified_new_user: dict, sean_gpt_host: str):
    # Insert two chats with different names.
    test_chat_name_1 = f"test{random.randint(0, 1000000)}"
    test_chat_name_2 = f"test{random.randint(0, 1000000)}"
    chat_response_1 = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name_1
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    chat_response_2 = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name_2
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # Test that the chat list can be filtered by name.
    query_params = {
        "name": test_chat_name_1
    }
    response_list = httpx.get(f"{sean_gpt_host}/chat", params=query_params, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response_1.json() in response_list.json()
    assert chat_response_2.json() not in response_list.json()
    # Test that the chat list can be filtered by id.
    query_params = {
        "id": chat_response_1.json()["id"]
    }
    response_list = httpx.get(f"{sean_gpt_host}/chat", params=query_params, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response_1.json() in response_list.json()
    assert chat_response_2.json() not in response_list.json()
    # clean up by deleting the chats
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response_1.json()["id"]
    })
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response_2.json()["id"]
    })

@describe(
""" Test that a user cannot modify a non-existent chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_modify_nonexistent_chat(verified_new_user: dict, sean_gpt_host: str):
    # Test that a chat cannot be updated if the chat id is not in the header.
    chat_response = httpx.put(f"{sean_gpt_host}/chat", json={
        "name": f"test{random.randint(0, 1000000)}"
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 422 Unprocessable Entity
    assert chat_response.status_code == 422, (
        f'incorrect status code: {chat_response.status_code}, response: {chat_response.json()}')

    # Test that a chat cannot be updated if the chat id is invalid.
    chat_response = httpx.put(f"{sean_gpt_host}/chat", json={
        "name": f"test{random.randint(0, 1000000)}"
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": "invalid"
    })
    # The response should be:
    # HTTP/1.1 404 Not Found
    # Content-Type: application/json
    # {
    #     "detail": "Chat not found"
    # }
    assert chat_response.status_code == 404, (
        f'incorrect status code: {chat_response.status_code}, response: {chat_response.json()}')
    assert chat_response.headers["content-type"] == "application/json"
    assert chat_response.json()["detail"] == "Chat not found"

@describe(
""" Test that a user can update a chat.

Only the name can be updated.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_update_chat(verified_new_user: dict, sean_gpt_host: str):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    create_chat_response = httpx.post(f"{sean_gpt_host}/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert create_chat_response.status_code == 201, (
        f'incorrect status code: {create_chat_response.status_code}, '
        f"response: {create_chat_response.json()}")

    # Update the chat name.
    new_test_chat_name = f"test{random.randint(0, 1000000)}"
    chat_response = httpx.put(f"{sean_gpt_host}/chat", json={
        "name": new_test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": create_chat_response.json()["id"]
    })
    # The response should be:
    # HTTP/1.1 204 No Content
    assert chat_response.status_code == 204, (
        f'incorrect status code: {chat_response.status_code}, response: {chat_response.json()}')
    # Clean up by deleting the chat.
    httpx.delete(f"{sean_gpt_host}/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": create_chat_response.json()["id"]
    })

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(verified_new_user: dict, sean_gpt_host: str):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    check_verified_route("POST", sean_gpt_host, "/chat", json={
        "name": test_chat_name
    }, verified_user=verified_new_user)
    check_verified_route("GET", sean_gpt_host, "/chat", verified_user=verified_new_user)
    # Check the PUT route
    # First, create the chat
    chat = httpx.post(f"{sean_gpt_host}/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    check_verified_route("PUT", sean_gpt_host, "/chat", json={
        "name": test_chat_name
    }, verified_user=verified_new_user, headers={
        "X-Chat-ID": chat["id"]
    })
    # Now check the DELETE route
    check_verified_route(
        "DELETE",
        sean_gpt_host,
        "/chat",
        verified_user=verified_new_user,
        headers={
            "X-Chat-ID": chat["id"]
        })
