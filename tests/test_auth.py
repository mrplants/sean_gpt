""" Tests for the auth endpoints.

The authentication is a valid Oauth2 implementation, so align the tests strictly
with the Oauth2 spec.

Authentication for this application is via unique email and referral token. A
referral token is unique for each pair of referrer and referee. The referrer can
be any user.  A referral token can be used only once.

The user database will come loaded with an admin user, which can be used to
create new users for testing.

This test file is intended to verify that all user authentication flows work
properly. It follows the lifecycle of a user:
- OAuth2 token generation.
- Token expiration.
- Referral code generation.
- New account creation.
- Referral code no longer valid.
- Account administration functions (password change, etc.)
- Account deletion.
- Denied access for authenticated endpoints.
"""
import random

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from sean_gpt.main import app
from sean_gpt.config import settings

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_auth_token() -> str:
    """ Get an auth token for testing.
    
    Returns:
        str: The auth token.
    """
    # Replace with your actual login endpoint and credentials
    # Generate a token
    response = client.post(
        "/auth/token",
        data={
            "grant_type": "password",
            "username": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    return response.json()["access_token"]

# OAuth2 token generation
def test_generate_token():
    """ Test that a token can be generated. """
    # Generate a token
    response = client.post(
        "/auth/token",
        data={
            "grant_type": "password",
            "username": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    # 
    # {
    # "access_token": "...",
    # "token_type": "bearer"
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["token_type"] == "bearer"
    assert type(response.json()["access_token"]) == str

# Token expiration.
def test_token_expiration(admin_auth_token: str):
    """ Test that a token expires. """
    # Check the expiration date of the token using JWT
    # The JWT expiration can be decoded and checked without the secret key.
    # Decode the token without verification
    unverified_claims = jwt.get_unverified_claims(response.json()["access_token"])
    assert unverified_claims["exp"] - unverified_claims["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    # Without waiting the full expiration time, it is not possible to write a
    # practical test for this.  Instead, we will perform a verified check
    # that the token will expire.
    decoded = jwt.decode(admin_auth_token, settings.secret_key, algorithms=[settings.algorithm])
    assert decoded["exp"] - decoded["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

# Referral code generation.
def test_referral_code_generation(admin_auth_token: str):
    """ Test that a referral code can be generated. """
    # Generate a referral code
    response = client.get(
        "/users/referral_code",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "referral_code": "..."
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert type(response.json()["referral_code"]) == str

# New account creation.
def test_new_account_creation(admin_auth_token: str):
    """ Test that a new account can be created. """
    # Get the admin user's ID
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    admin_user_id = response.json()["id"]
    # Get a referral code
    response = client.get(
        "/users/referral_code",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    referral_code = response.json()["referral_code"]
    # Create a new user with random email and password
    response = client.post(
        "/users/",
        json={
            "email": f"test{random.randint(0, 1000000)}@test.com",
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
    # "email": "...",
    # "referrer_user_id": "...",
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert type(response.json()["id"]) == str
    assert type(response.json()["email"]) == str
    assert response.json()["referrer_user_id"] == admin_user_id