##########
# /users #
##########
# POST (protected):  Create a user
# GET (protected):  Get a user's info
# DELETE (protected):  Delete a user's account

from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

from .fixtures import *
from ..util import *

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(referral_code: str, verified_new_user: dict, client: TestClient):
    check_authorized_route("POST", "/users", {
        "phone": f"+{random.randint(10000000000, 20000000000)}",
        "password": f"test{random.randint(0, 1000000)}",
        "referral_code": referral_code
    }, authorized_user=verified_new_user, client=client)
    check_authorized_route("GET", "/users", authorized_user=verified_new_user, client=client)
    check_authorized_route("DELETE", "/users", authorized_user=verified_new_user, client=client)

@describe(""" Test that a new account can be created. """)
def test_new_account_creation(admin_user: dict, client: TestClient):
    # Get the admin user's ID
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_user['access_token']}"}
    )
    admin_user_id = response.json()["id"]
    # Get a referral code
    response = client.get(
        f"/users/referral_code",
        headers={"Authorization": f"Bearer {admin_user['access_token']}"}
    )
    referral_code = response.json()["referral_code"]
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    response = client.post(
        "/users",
        json={
            "phone": test_new_user_phone,
            "password": f"test{random.randint(0, 1000000)}",
            "referral_code": referral_code
        }
    )
    # The response should be:
    # HTTP/1.1 201 Created
    # Content-Type: application/json
    #
    # {
    # "id": "...",
    # "phone": "...",
    # "referrer_user_id": "...",
    # "is_phone_verified": false
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert type(response.json()["id"]) == str
    assert response.json()["phone"] == test_new_user_phone
    assert response.json()["referrer_user_id"] == admin_user_id
    assert response.json()["is_phone_verified"] == False

@describe(""" Test that a new account cannot be created with an incorrect referral code. """)
def test_new_account_creation_incorrect_referral_code(client: TestClient):
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    response = client.post(
        "/users",
        json={
            "phone": test_new_user_phone,
            "password": f"test{random.randint(0, 1000000)}",
            "referral_code": "incorrect_referral_code"
        }
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to create user:  Referral code is incorrect."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to create user:  Referral code is incorrect."

@describe(""" Test that a new account cannot be created with an existing phone. """)
def test_new_account_creation_existing_phone(referral_code: str, client: TestClient):
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    client.post(
        "/users/",
        json={
            "phone": test_new_user_phone,
            "password": f"test{random.randint(0, 1000000)}",
            "referral_code": referral_code
        }
    )
    # Create a new user with the same phone
    response = client.post(
        "/users",
        json={
            "phone": test_new_user_phone,
            "password": f"test{random.randint(0, 1000000)}",
            "referral_code": referral_code
        }
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to create user:  Phone already exists."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to create user:  Phone already exists."

@describe(""" Test that a user's info can be retrieved. """)
def test_get_user_info(verified_new_user: dict, client: TestClient):
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "id": "...",
    # "phone": "...",
    # "referrer_user_id": "...",
    # "is_phone_verified": true
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["id"] == verified_new_user["id"]
    assert response.json()["phone"] == verified_new_user["phone"]
    assert response.json()["referrer_user_id"] == verified_new_user["referrer_user_id"]
    assert response.json()["is_phone_verified"] == True

@describe(""" Test that a user's account can be deleted. """)
def test_delete_user(verified_new_user: dict, client: TestClient):
    response = client.delete(
        "/users",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert response.status_code == 204
    # Check that the user's account was deleted
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to validate credentials"
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to validate credentials"