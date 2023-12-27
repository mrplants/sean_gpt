###################
# /users/password #
###################
# PUT (protected): Change the user's password

from fastapi.testclient import TestClient

from sean_gpt.main import app
from sean_gpt.util.describe import describe

from .fixtures import *

client = TestClient(app)

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(new_user: str):
    check_authorized_route("PUT", "/users/password", {
        "new_password": f"test{random.randint(0, 1000000)}",
        "old_password": new_user["password"]
    })

@describe(""" Test that a user's password can be changed. """)
def test_password_change(new_user: dict):
    # Change the user's password
    new_password = f"new_password{random.randint(0, 1000000)}"
    response = client.put(
        "/users/password",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={
            "new_password": new_password,
            "old_password": new_user["password"]
        }
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert response.status_code == 204
    # Check that the user can log in with the new password
    response = client.post(
        "/users/token",
        data={
            "grant_type": "password",
            "username": new_user["phone"],
            "password": new_password,
        },
    )
    assert response.status_code == 200
    # Check that the user cannot log in with the old password
    response = client.post(
        "/users/token",
        data={
            "grant_type": "password",
            "username": new_user["phone"],
            "password": new_user["password"],
        },
    )
    assert response.status_code == 400


@describe(""" Test that a user's password cannot be changed with an incorrect password. """)
def test_password_change_incorrect_password(new_user: dict):
    # Change the user's password
    new_password = f"new_password{random.randint(0, 1000000)}"
    response = client.put(
        "/users/password",
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
    # "detail": "Unable to validate credentials."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to change password:  Incorrect password."