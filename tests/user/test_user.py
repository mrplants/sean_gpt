""" Tests the /user endpoint.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

##########
# /user #
##########
# POST (protected):  Create a user
# GET (protected):  Get a user's info
# DELETE (protected):  Delete a user's account
#
# TODO: Missing Tests
# - Test that a user with no password hash is prompted to reset their password.
# - Test that a user resetting their password is sent a temporary password via SMS.
# - Test that the temporary password expires.
# - Test that a user with a temporary password is prompted to reset their password.
# - Test that SQL injection is not possible.
import random

import httpx

from sean_gpt.util.describe import describe

from ..util.check_routes import check_authorized_route

@describe(""" Test that a new account can be created. """)
def test_new_account_creation(admin_user: dict, sean_gpt_host: str):
    admin_user_id = admin_user["id"]
    referral_code = admin_user["referral_code"]
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    test_new_user_password = f"test{random.randint(0, 1000000)}"
    response = httpx.post(
        f"{sean_gpt_host}/user",
        json={
            "user": {
                "phone": test_new_user_phone,
                "password": test_new_user_password,
            },
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
    # "is_phone_verified": false,
    # "opted_into_sms": false,
    # }
    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json", "Response should be JSON."
    assert isinstance(response.json()["id"], str), "User id should be a string."
    assert response.json()["phone"] == test_new_user_phone
    assert response.json()["referrer_user_id"] == admin_user_id
    # TODO: Re-enable this when Twilio campaign is ready
    # assert not response.json()["is_phone_verified"]
    # delete the new user.  Need to get teh access token first
    token_response = httpx.post(
        f"{sean_gpt_host}/user/token",
        data={
            "grant_type": "password",
            "username": test_new_user_phone,
            "password": test_new_user_password,
        }
    )
    httpx.delete(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {token_response.json()['access_token']}"}
    )

@describe(""" Test that a new account cannot be created with an incorrect referral code. """)
def test_new_account_creation_incorrect_referral_code(sean_gpt_host: str):
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    test_new_user_password = f"test{random.randint(0, 1000000)}"
    response = httpx.post(
        f"{sean_gpt_host}/user",
        json={
            "user": {
                "phone": test_new_user_phone,
                "password": test_new_user_password,
            },
            "referral_code": "incorrect_referral_code"
        }
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to create user:  Referral code does not exist."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to create user:  Referral code does not exist."

@describe(""" Test that a new account cannot be created with an existing phone. """)
def test_new_account_creation_existing_phone(referral_code: str, sean_gpt_host: str):
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    test_new_user_password = f"test{random.randint(0, 1000000)}"
    httpx.post(
        f"{sean_gpt_host}/user",
        json={
            "user": {
                "phone": test_new_user_phone,
                "password": test_new_user_password,
            },
            "referral_code": referral_code
        }
    )
    # Create a new user with the same phone
    response = httpx.post(
        f"{sean_gpt_host}/user",
        json={
            "user": {
                "phone": test_new_user_phone,
                "password": f"test{random.randint(0, 1000000)}",
            },
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
    # Clean up the new user. Need to get the access token first
    token_response = httpx.post(
        f"{sean_gpt_host}/user/token",
        data={
            "grant_type": "password",
            "username": test_new_user_phone,
            "password": test_new_user_password,
        }
    )
    httpx.delete(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {token_response.json()['access_token']}"}
    )

@describe(""" Test that a user's info can be retrieved. """)
def test_get_user_info(new_user: dict, sean_gpt_host: str):
    response = httpx.get(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "id": "...",
    # "phone": "...",
    # "referrer_user_id": "...",
    # "is_phone_verified": false
    # "opted_into_sms": false,
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["id"] == new_user["id"]
    assert response.json()["phone"] == new_user["phone"]
    assert response.json()["referrer_user_id"] == new_user["referrer_user_id"]
    # TODO: Re-enable this when Twilio campaign is ready
    # assert not response.json()["is_phone_verified"]

@describe(""" Test that a user's account can be deleted. """)
def test_delete_user(new_user: dict, sean_gpt_host: str):
    response = httpx.delete(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert response.status_code == 204
    # Check that the user's account was deleted
    response = httpx.get(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 401 Unauthorized
    # Content-Type: application/json
    #
    # {
    # "detail": "Could not validate credentials"
    # }
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Could not validate credentials"

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(
    referral_code: str,
    verified_new_user: dict,
    sean_gpt_host: str):
    check_authorized_route("POST", sean_gpt_host, "/user", json={
        "user": {
            "phone": f"+{random.randint(10000000000, 20000000000)}",
            "password": f"test{random.randint(0, 1000000)}",
        },
        "referral_code": referral_code
    }, authorized_user=verified_new_user)
    check_authorized_route("GET", sean_gpt_host,"/user", authorized_user=verified_new_user)
    check_authorized_route("DELETE", sean_gpt_host, "/user", authorized_user=verified_new_user)
