##########
# /chat #
##########
# POST (protected, verified):  Create a new chat
# PUT (protected, verified):  Update a chat, UUID in header.
# GET (protected, verified):  Get a list of chats, filters in query string.
# DELETE (protected, verified):  Delete a chat, UUID in header.

from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

from ..user.fixtures import *
from ..util import *

@describe(
""" Test that a user can create a chat. 

The chat name is optional.  Test that it works with and without a name.  After
creating the chat, test that it appears in the list of chats for the user.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_chat(verified_new_user: dict, client: TestClient):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response_1 = client.post("/chat", json={
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
    #     "assistant_id": "..."
    # }
    assert chat_response_1.status_code == 201
    assert chat_response_1.headers["content-type"] == "application/json"
    assert chat_response_1.json()["name"] == test_chat_name
    assert type(chat_response_1.json()["id"]) == str
    assert chat_response_1.json()["user_id"] == verified_new_user["id"]
    assert type(chat_response_1.json()["assistant_id"]) == str

    # Create a chat without a name.
    chat_response_2 = client.post("/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    # {
    #     "name": "",
    #     "id": "...",
    #     "user_id": "...",
    #     "assistant_id": "..."
    # }
    assert chat_response_2.status_code == 201
    assert chat_response_2.headers["content-type"] == "application/json"
    assert chat_response_2.json()["name"] == ""
    assert type(chat_response_2.json()["id"]) == str
    assert chat_response_2.json()["user_id"] == verified_new_user["id"]
    assert type(chat_response_2.json()["assistant_id"]) == str

    # Check that both chats appears in the list of chats for the user.
    response_list = client.get("/chat", headers={
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
    #         "assistant_id": "..."
    #     },...
    # ]
    assert response_list.status_code == 200
    assert response_list.headers["content-type"] == "application/json"
    assert chat_response_1.json() in response_list.json()
    assert chat_response_2.json() in response_list.json()

@describe(
""" Test that a user can delete a chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_delete_chat(verified_new_user: dict, client: TestClient):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response = client.post("/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.status_code == 201

    # Delete the chat.
    delete_response = client.delete("/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response.json()["id"]
    })
    # The response should be:
    # HTTP/1.1 204 No Content
    assert delete_response.status_code == 204

    # Check that the chat no longer appears in the list of chats for the user.
    response_list = client.get("/chat", headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.json() not in response_list.json()        

@describe(
""" Test that a user can get a list of chats.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_get_chat_list(verified_new_user: dict, client: TestClient):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response = client.post("/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.status_code == 201

    # Check that the chat appears in the list of chats for the user.
    response_list = client.get("/chat", headers={
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
    #         "assistant_id": "..."
    #     },...
    # ]
    assert response_list.status_code == 200
    assert response_list.headers["content-type"] == "application/json"
    assert chat_response.json() in response_list.json()

@describe(
""" Test that a user can filter the list of chats.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_filter_chat_list(verified_new_user: dict, client: TestClient):
    # Insert two chats with different names.
    test_chat_name_1 = f"test{random.randint(0, 1000000)}"
    test_chat_name_2 = f"test{random.randint(0, 1000000)}"
    chat_response_1 = client.post("/chat", json={
        "name": test_chat_name_1
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    chat_response_2 = client.post("/chat", json={
        "name": test_chat_name_2
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # Test that the chat list can be filtered by name.
    query_params = {
        "name": test_chat_name_1
    }
    response_list = client.get("/chat", params=query_params, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response_1.json() in response_list.json()
    assert chat_response_2.json() not in response_list.json()
    # Test that the chat list can be filtered by id.
    query_params = {
        "id": chat_response_1.json()["id"]
    }
    response_list = client.get("/chat", params=query_params, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response_1.json() in response_list.json()
    assert chat_response_2.json() not in response_list.json()

@describe(
""" Test that a user cannot modify a non-existent chat.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_modify_nonexistent_chat(verified_new_user: dict, client: TestClient):
    # Test that a chat cannot be updated if the chat id is not in the header.
    chat_response = client.put("/chat", json={
        "name": f"test{random.randint(0, 1000000)}"
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    #     "detail": "Chat ID not provided."
    # }
    assert chat_response.status_code == 400
    assert chat_response.headers["content-type"] == "application/json"
    assert chat_response.json()["detail"] == "Chat ID not provided."

    # Test that a chat cannot be updated if the chat id is invalid.
    chat_response = client.put("/chat", json={
        "name": f"test{random.randint(0, 1000000)}"
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": "invalid"
    })
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    #     "detail": "Chat ID invalid."
    # }
    assert chat_response.status_code == 400
    assert chat_response.headers["content-type"] == "application/json"
    assert chat_response.json()["detail"] == "Chat ID invalid."

@describe(
""" Test that a user can update a chat.

Only the name can be updated.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_update_chat(verified_new_user: dict, client: TestClient):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    # Create a chat with a name.
    chat_response = client.post("/chat", json={
        "name": test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}"
    })
    assert chat_response.status_code == 201

    # Update the chat name.
    new_test_chat_name = f"test{random.randint(0, 1000000)}"
    chat_response = client.put("/chat", json={
        "name": new_test_chat_name
    }, headers={
        "Authorization": f"Bearer {verified_new_user['access_token']}",
        "X-Chat-ID": chat_response.json()["id"]
    })
    # The response should be:
    # HTTP/1.1 204 No Content
    assert chat_response.status_code == 204

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(verified_new_user: dict, client: TestClient):
    test_chat_name = f"test{random.randint(0, 1000000)}"
    check_verified_route("POST", "/chat", json={
        "name": test_chat_name
    }, verified_user=verified_new_user, client=client)
    check_verified_route("GET", "/chat", verified_user=verified_new_user, client=client)
    check_verified_route("DELETE", "/chat", json={
        "name": test_chat_name
    }, verified_user=verified_new_user, client=client)