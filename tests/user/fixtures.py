""" These are utility functions and test fixtures for auth testing.

Other endpoints requiring authorization for access can uses these functions and
test fixtures to verify that the authorization is working as expected.
"""
import random
import re
from unittest.mock import patch, Mock

import pytest
from fastapi.testclient import TestClient

from sean_gpt.config import settings, constants
from sean_gpt.util.describe import describe
from ..util import *

@describe(""" Test fixture to provide an admin auth token. """)
@pytest.fixture
def admin_auth_token(client: TestClient) -> str:
    # Generate a token
    response = client.post(
        f"/user/token",
        data={
            "grant_type": "password",
            "username": settings.admin_phone,
            "password": settings.admin_password,
        },
    )
    return response.json()["access_token"]

@describe(""" Test fixture to provide an admin user. """)
@pytest.fixture
def admin_user(admin_auth_token: str, client: TestClient) -> dict:
    # Get the admin user
    response = client.get(
        "/user",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json() | {"access_token": admin_auth_token}

@describe(""" Test fixture to provide a valid referral code. """)
@pytest.fixture
def referral_code(admin_auth_token: str, client: TestClient) -> str:
    # Get a referral code
    response = client.get(
        "/user/referral_code",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json()["referral_code"]

@describe(""" Test fixture to provide a new user and their auth token. """)
@pytest.fixture
def new_user(referral_code: str, client: TestClient) -> dict:
    # Create a new user with random phone and password
    new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    new_user_password = f"test{random.randint(0, 1000000)}"
    response_user = client.post(
        "/user",
        json={
            "user": {
                "phone": new_user_phone,
                "password": new_user_password,
            },
            "referral_code": referral_code
        }
    )
    # Get the new user's auth token
    response_token = client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": new_user_phone,
            "password": new_user_password,
        },
    )
    yield response_user.json() | response_token.json() | {"password": new_user_password}
    # Delete the new user as cleanup
    client.delete(
        "/user",
        headers={"Authorization": f"Bearer {response_token.json()['access_token']}"}
    )

@describe(""" Test fixture to mock the Twilio SMS function. """)
@pytest.fixture
def mock_twilio_sms_create(client: TestClient) -> Mock:
    with patch('twilio.rest.api.v2010.account.message.MessageList.create') as mock_message_create:
        yield mock_message_create

@describe(""" Test fixture to provide a verified new user and their auth token. """)
@pytest.fixture
def verified_new_user(new_user: dict, mock_twilio_sms_create: Mock, client: TestClient) -> dict:
    # Request new user verification code
    client.post(
        f"/user/request_phone_verification",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    code_message_regex = constants.phone_verification_message.format('(\\S+)').replace('.', '\\.')
    phone_verification_code = re.search(code_message_regex, mock_twilio_sms_create.call_args[1]["body"]).group(1)
    # Verify the user
    response_token = client.put(
        f"/user/is_phone_verified",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"phone_verification_code": phone_verification_code}
    )
    yield new_user

@describe(""" Checks that a route requires authorization for access. """)
def check_authorized_route(request_type: str, route: str, authorized_user: dict, client: TestClient, **request_args):
    request_func = {
        "get": client.get,
        "post": client.post,
        "put": client.put,
        "delete": client.delete
    }[request_type.lower()]
    response = request_func(
        route,
        headers={"Authorization": f"Bearer {authorized_user['access_token']}"},
        **request_args
    )
    # The response should be any 2xx response code
    assert response.status_code // 100 == 2, f"Expected status code 2xx, got {response.status_code}. Response body: {response.content}"
    # Now send an unauthorized request
    response = client.post(
        route,
        headers={"Authorization": f"Bearer invalid_token"},
        **request_args
    )
    # The response should not be a 2xx response code
    assert response.status_code // 100 != 2, f"Expected status code NOT 2xx, got {response.status_code}. Response body: {response.content}"

@describe(""" Checks that a route requires a verified user for access. """)
def check_verified_route(request_type: str, route: str, verified_user: dict, client: TestClient, **request_args):
    # First, create an unverified user from the referral code of the verified user
    new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    new_user_password = f"test{random.randint(0, 1000000)}"
    unverified_user = client.post(
        "/user",
        json={
            "user": {
                "phone": new_user_phone,
                "password": new_user_password,
            },
            "referral_code": verified_user['referral_code']
        }
    ).json()
    # Get the new user's auth token
    unverified_user = unverified_user | client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": new_user_phone,
            "password": new_user_password,
        },
    ).json() | {"password": new_user_password}

    request_func = {
        "get": client.get,
        "post": client.post,
        "put": client.put,
        "delete": client.delete
    }[request_type.lower()]
    response = request_func(
        route,
        headers={"Authorization": f"Bearer {verified_user['access_token']}"},
        **request_args
    )
    # The response should be any 2xx response code
    assert response.status_code // 100 == 2, f"Expected status code 2xx, got {response.status_code}. Response body: {response.text}"
    # Now send an unverified request
    response = request_func(
        route,
        headers={"Authorization": f"Bearer {unverified_user['access_token']}"},
        **request_args
    )
    # The response should not be a 2xx response code
    assert response.status_code // 100 != 2, f"Expected status code NOT 2xx, got {response.status_code}. Response body: {response.text}"
