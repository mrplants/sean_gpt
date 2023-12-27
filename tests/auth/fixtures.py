""" These are utility functions and test fixtures for auth testing.

Other endpoints requiring authorization for access can uses these functions and
test fixtures to verify that the authorization is working as expected.
"""
import random
import pytest
import re
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from jose import jwt

from sean_gpt.main import app
from sean_gpt.config import settings
from sean_gpt import constants
from sean_gpt.util.describe import describe

client = TestClient(app)

@describe(""" Test fixture to provide an admin auth token. """)
@pytest.fixture(scope="module")
def admin_auth_token() -> str:
    # Generate a token
    response = client.post(
        f"/users/token",
        data={
            "grant_type": "password",
            "username": settings.ADMIN_PHONE,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    return response.json()["access_token"]

def admin_user(admin_auth_token: str) -> dict:
    # Get the admin user
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json() | {"access_token": admin_auth_token}

@describe(""" Test fixture to provide a valid referral code. """)
@pytest.fixture(scope="function")
def referral_code(admin_auth_token: str) -> str:
    # Get a referral code
    response = client.get(
        "/users/referral_code",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json()["referral_code"]

@describe(""" Test fixture to provide a new user and their auth token. """)
@pytest.fixture(scope="function")
def new_user(referral_code: str) -> dict:
    # Create a new user with random phone and password
    new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    new_user_password = f"test{random.randint(0, 1000000)}"
    response_user = client.post(
        "/users/",
        json={
            "phone": new_user_phone,
            "password": new_user_password,
            "referral_code": referral_code
        }
    )
    # Get the new user's auth token
    response_token = client.post(
        "/auth/token",
        data={
            "grant_type": "password",
            "username": new_user_phone,
            "password": new_user_password,
        },
    )
    yield response_user.json() | response_token.json() | {"password": new_user_password}
    # TODO: Delete the new user as cleanup

@describe(""" Test fixture to mock the Twilio SMS function. """)
@pytest.fixture(scope="module")
def mock_twilio_sms_create() -> Mock:
    with patch('twilio.rest.Client.messages.create') as mock_message_create:
        yield mock_message_create

@describe(""" Test fixture to provide a verified new user and their auth token. """)
@pytest.fixture(scope="function")
def verified_new_user(new_user: dict, mock_twilio_sms_create: Mock) -> dict:
    # Request new user verification code
    client.post(
        f"/users/request_phone_verification",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    code_message_regex = constants.PHONE_VERIFICATION_MESSAGE.format('(\\S+)').replace('.', '\\.')
    phone_verification_code = re.search(code_message_regex, mock_twilio_sms_create.call_args[1]["body"]).group(1)
    # Verify the user
    response_token = client.put(
        f"/users/is_phone_verified",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"phone_verification_code": phone_verification_code}
    )
    yield new_user

@describe(""" Checks that a route requires authorization for access. """)
def check_authorized_route(request_type: str, route: str, verified_new_user: dict, json_payload: dict = {}):
    request_func = {
        "get": client.get,
        "post": client.post,
        "put": client.put,
        "delete": client.delete
    }[request_type.lower()]
    response = request_func(
        route,
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json=json_payload
    )
    # The response should be any 2xx response code
    assert response.status_code // 100 == 2
    # Now send an unauthorized request
    response = client.post(
        route,
        headers={"Authorization": f"Bearer invalid_token"},
        json=json_payload
    )
    # The response should not be a 2xx response code
    assert response.status_code // 100 != 2

@describe(""" Checks that a route requires a verified user for access. """)
def check_verified_route(request_type: str, route: str, verified_new_user: dict, new_user: dict, json_payload: dict = {}):
    request_func = {
        "get": client.get,
        "post": client.post,
        "put": client.put,
        "delete": client.delete
    }[request_type.lower()]
    response = request_func(
        route,
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json=json_payload
    )
    # The response should be any 2xx response code
    assert response.status_code // 100 == 2
    # Now send an unverified request
    response = request_func(
        route,
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json=json_payload
    )
    # The response should not be a 2xx response code
    assert response.status_code // 100 != 2