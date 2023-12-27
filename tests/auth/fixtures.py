""" These are utility functions and test fixtures for auth testing.

Other endpoints requiring authorization for access can uses these functions and
test fixtures to verify that the authorization is working as expected.
"""
import random
import pytest

from fastapi.testclient import TestClient
from jose import jwt

from sean_gpt.main import app
from sean_gpt.config import settings
from sean_gpt.util.describe import describe

client = TestClient(app)

@describe(""" Test fixture to provide an admin auth token. """)
@pytest.fixture(scope="module")
def admin_auth_token() -> str:
    # Generate a token
    response = client.post(
        "/auth/token",
        data={
            "grant_type": "password",
            "username": settings.ADMIN_PHONE,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    return response.json()["access_token"]

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

@describe(""" Test fixture to provide a verified new user and their auth token. """)
@pytest.fixture(scope="function")
def verified_new_user(new_user: dict) -> dict:
    phone_verification_code = f'{random.randint(100000, 999999)}'
    # Mock the twilio client
    # Verify the new user
    response = client.post(
        "/auth/request_phone_verification",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    # Get the new user's auth token
    response_token = client.put(
        "/users/is_phone_verified",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"phone_verification_code": phone_verification_code}
    )
    yield new_user