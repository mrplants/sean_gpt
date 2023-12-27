""" Tests for the auth endpoints.

The authentication is a valid Oauth2 implementation, so align the tests strictly
with the Oauth2 spec.

The user database will come loaded with an admin user, which can be used to
create new users for testing.

Many endpoints are unavailable while the user's phone is not verified.  This
will be tested by attempting to access those endpoints before and after
verifying the phone.

This test file is intended to verify that all user authentication flows work
properly. It follows the lifecycle of a user:
- OAuth2 token generation.
- Token expiration.
- Referral code generation.
- New account creation.
- Account administration functions:
    - Phone verification.
    - Password change.
- Denied access for authenticated endpoints.
"""
import random

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from sean_gpt.main import app
from sean_gpt.config import settings
from sean_gpt.util.describe import describe
from .fixtures import admin_auth_token, new_user, referral_code

client = TestClient(app)

@describe(""" Test that an authorization token can be generated. """)
def test_generate_token():
    # Generate a token
    response = client.post(
        "/auth/token",
        data={
            "grant_type": "password",
            "username": settings.ADMIN_PHONE,
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

@describe(""" Test that an authorization token will expire. """)
def test_token_expiration(admin_auth_token: str):
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

@describe(""" Test that a referral code can be generated. """)
def test_referral_code_generation(admin_auth_token: str):
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

@describe(""" Test that a referral code cannot be generated for an unverified user. """)
def test_referral_code_generation_unverified(new_user: dict):
    # Generate a referral code
    response = client.get(
        "/users/referral_code",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 401 Unauthorized
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to generate referral code:  User phone is not verified."
    # }
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to generate referral code:  User phone is not verified."

@describe(""" Test that a new account can be created. """)
def test_new_account_creation(admin_auth_token: str):
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
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    response = client.post(
        "/users/",
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
def test_new_account_creation_incorrect_referral_code():
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    response = client.post(
        "/users/",
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
def test_new_account_creation_existing_phone(referral_code: str):
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
        "/users/",
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

@describe(""" Test that a user's phone can be verified.

A user's phone is verified with this flow:
- User requests a verification code.
- Verification code is sent to the user's phone.
- User submits the verification code.

Here, we will mock the twilio client to return a known verification code.
""")
def test_phone_verification(admin_auth_token: str):
    # Get a verification code
    response = client.get(
        "/users/verify",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    # Create a new user with random phone and password
    test_new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    response = client.post(
        "/users/",
        json={
            "phone": test_new_user_phone,
            "password": f"test{random.randint(0, 1000000)}",
            "referral_code": referral_code
        }
    )
    # Mock the twilio client
    from sean_gpt import auth
    auth.twilio_client = auth.MockTwilioClient()
    # Request a verification code
    response = client.post(
        "/auth/phone_verification",
        json={
            "phone": test_new_user_phone
        }
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "detail": "Verification code sent."
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Verification code sent."
    # Submit the verification code
    response = client.post(
        "/auth/phone_verification",
        json={
            "phone": test_new_user_phone,
            "verification_code": "123456"
        }
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "detail": "Phone verified."
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Phone verified."
    # Check that the user's phone is verified
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    assert response.json()["is_phone_verified"] == True