""" Tests for the user/password route.
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

##################
# /user/password #
##################
# PUT (protected): Change the user's password

import random

import httpx

from sean_gpt.util.describe import describe

from ..util.check_routes import check_authorized_route

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(verified_new_user: str, sean_gpt_host: str):
    check_authorized_route("PUT", sean_gpt_host, "/user/password", json={
        "new_password": f"test{random.randint(0, 1000000)}",
        "old_password": verified_new_user["password"]
    }, authorized_user=verified_new_user)

@describe(""" Test that a user's password can be changed. """)
def test_password_change(new_user: dict, sean_gpt_host: str):
    # Change the user's password
    new_password = f"new_password{random.randint(0, 1000000)}"
    response = httpx.put(
        f"{sean_gpt_host}/user/password",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={
            "new_password": new_password,
            "old_password": new_user["password"]
        }
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert response.status_code == 204, (
        f"Status should be 204, not {response.status_code}. Response: {response.text}")
    # Check that the user can log in with the new password
    response = httpx.post(
        f"{sean_gpt_host}/user/token",
        data={
            "grant_type": "password",
            "username": new_user["phone"],
            "password": new_password,
        },
    )
    assert response.status_code == 200, (
        f"Status should be 200, not {response.status_code}. Response: {response.text}")
    # Check that the user cannot log in with the old password
    response = httpx.post(
        f"{sean_gpt_host}/user/token",
        data={
            "grant_type": "password",
            "username": new_user["phone"],
            "password": new_user["password"],
        },
    )
    assert response.status_code == 401, (
        f"Status should be 401, not {response.status_code}. Response: {response.text}")


@describe(""" Test that a user's password cannot be changed with an incorrect password. """)
def test_password_change_incorrect_password(new_user: dict, sean_gpt_host: str):
    # Change the user's password
    new_password = f"new_password{random.randint(0, 1000000)}"
    response = httpx.put(
        f"{sean_gpt_host}/user/password",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={
            "new_password": new_password,
            "old_password": "incorrect_password"
        }
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to change password:  Incorrect password."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to change password:  Incorrect password."
